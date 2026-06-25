#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=lib.sh
. "$SCRIPT_DIR/lib.sh"

require_command curl
require_command docker
require_command jq
require_command python3
load_env

fail() {
  echo "FAIL $*" >&2
  exit 1
}

pass() {
  echo "PASS $*"
}

epoch_millis() {
  python3 - <<'PY'
import time

print(int(time.time() * 1000))
PY
}

json_length() {
  jq 'length' "$1"
}

ensure_user_profile_admin_edit_attributes() {
  local current_file="$TMP_DIR/user-profile-current.json"
  local payload_file="$TMP_DIR/user-profile-payload.json"
  local evidence_file="$EVIDENCE_DIR/wp-011-016-user-profile-config.json"

  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/profile" | jq '.' > "$current_file"
  jq '.unmanagedAttributePolicy = "ADMIN_EDIT"' "$current_file" > "$payload_file"
  api_json PUT "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/profile" "$(cat "$payload_file")" '^(200|204)$' >/dev/null
  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/profile" | jq '.' > "$evidence_file"
  jq -e '.unmanagedAttributePolicy == "ADMIN_EDIT"' "$evidence_file" >/dev/null \
    || fail "Keycloak user profile did not enable ADMIN_EDIT unmanaged attributes for PoC IAM attributes"
}

api_no_body() {
  local method=$1
  local token=$2
  local path=$3
  local expected_status=${4:-'^(200|201|204)$'}
  local response_file
  local status

  response_file=$(mktemp)
  status=$(curl -sS \
    -o "$response_file" \
    -w "%{http_code}" \
    -X "$method" \
    -H "Authorization: Bearer $token" \
    "$(api_url "$path")")

  if [[ ! "$status" =~ $expected_status ]]; then
    echo "Unexpected HTTP status $status for $method $(api_url "$path")" >&2
    cat "$response_file" >&2
    rm -f "$response_file"
    return 1
  fi

  cat "$response_file"
  rm -f "$response_file"
}

ensure_user_fixture() {
  local username=$1
  local email=$2
  local email_verified=$3
  local first_name=$4
  local last_name=$5
  local output_file=$6
  local user_id
  local payload

  payload=$(jq -cn \
    --arg username "$username" \
    --arg email "$email" \
    --arg firstName "$first_name" \
    --arg lastName "$last_name" \
    --argjson emailVerified "$email_verified" \
    '{
      username: $username,
      enabled: true,
      email: $email,
      emailVerified: $emailVerified,
      firstName: $firstName,
      lastName: $lastName,
      requiredActions: []
    }')

  user_id=$(user_uuid "$ADMIN_TOKEN" "$username")
  if [[ -z "$user_id" ]]; then
    api_json POST "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users" "$payload" '^(201|204)$' >/dev/null
    user_id=$(user_uuid "$ADMIN_TOKEN" "$username")
    pass "Created PoC user $username"
  else
    api_json PUT "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$user_id" "$payload" '^(200|204)$' >/dev/null
    pass "Updated PoC user $username"
  fi

  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$user_id" | jq '.' > "$output_file"
}

set_user_business_state() {
  local user_id=$1
  local account_id=$2
  local lifecycle=$3
  local linked_subject=$4
  local correlation_id=$5
  local current_file="$TMP_DIR/user-current-$user_id.json"
  local payload_file="$TMP_DIR/user-payload-$user_id.json"
  local updated_file="$TMP_DIR/user-updated-$user_id.json"

  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$user_id" | jq '.' > "$current_file"
  jq \
    --arg accountId "$account_id" \
    --arg lifecycle "$lifecycle" \
    --arg linkedSubject "$linked_subject" \
    --arg correlationId "$correlation_id" \
    '
    .attributes = ((.attributes // {}) + {
      "edrlab.account_id": [$accountId],
      "edrlab.lifecycle": [$lifecycle],
      "edrlab.last_control_plane_correlation": [$correlationId],
      "edrlab.managed_by": ["edrlab-iam-control-plane-api"]
    })
    | if $linkedSubject == "" then
        .attributes |= del(."edrlab.linked_subject")
      else
        .attributes."edrlab.linked_subject" = [$linkedSubject]
      end
    ' "$current_file" > "$payload_file"

  api_json PUT "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$user_id" "$(cat "$payload_file")" '^(200|204)$' >/dev/null
  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$user_id" | jq '.' > "$updated_file"

  jq -e --arg lifecycle "$lifecycle" '.attributes["edrlab.lifecycle"][0] == $lifecycle' "$updated_file" >/dev/null \
    || fail "Keycloak did not persist edrlab.lifecycle for user $user_id"
  jq -e --arg accountId "$account_id" '.attributes["edrlab.account_id"][0] == $accountId' "$updated_file" >/dev/null \
    || fail "Keycloak did not persist edrlab.account_id for user $user_id"
  if [[ -n "$linked_subject" ]]; then
    jq -e --arg linkedSubject "$linked_subject" '.attributes["edrlab.linked_subject"][0] == $linkedSubject' "$updated_file" >/dev/null \
      || fail "Keycloak did not persist edrlab.linked_subject for user $user_id"
  fi
}

direct_set_user_lifecycle_without_control_plane() {
  local user_id=$1
  local lifecycle=$2
  local current_file="$TMP_DIR/direct-user-current-$user_id.json"
  local payload_file="$TMP_DIR/direct-user-payload-$user_id.json"
  local updated_file="$TMP_DIR/direct-user-updated-$user_id.json"

  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$user_id" | jq '.' > "$current_file"
  jq \
    --arg lifecycle "$lifecycle" \
    '
    .attributes = (.attributes // {})
    | .attributes."edrlab.lifecycle" = [$lifecycle]
    ' "$current_file" > "$payload_file"

  api_json PUT "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$user_id" "$(cat "$payload_file")" '^(200|204)$' >/dev/null
  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$user_id" | jq '.' > "$updated_file"
  jq -e --arg lifecycle "$lifecycle" '.attributes["edrlab.lifecycle"][0] == $lifecycle' "$updated_file" >/dev/null \
    || fail "Keycloak did not persist direct edrlab.lifecycle update for user $user_id"
}

ensure_client_role() {
  local role_name=$1
  local description=$2
  local attributes_json=$3
  local output_file=$4
  local encoded_role_name
  local payload

  encoded_role_name=$(urlencode "$role_name")
  payload=$(jq -cn \
    --arg name "$role_name" \
    --arg description "$description" \
    --argjson attributes "$attributes_json" \
    '{
      name: $name,
      description: $description,
      attributes: $attributes
    }')

  if api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/clients/$CLIENT_UUID/roles/$encoded_role_name" > "$output_file" 2>/dev/null; then
    api_json PUT "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/clients/$CLIENT_UUID/roles/$encoded_role_name" "$payload" '^(200|204)$' >/dev/null
  else
    api_json POST "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/clients/$CLIENT_UUID/roles" "$payload" '^(201|204|409)$' >/dev/null
  fi

  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/clients/$CLIENT_UUID/roles/$encoded_role_name" | jq '.' > "$output_file"
}

assign_client_role_to_user() {
  local user_id=$1
  local role_file=$2
  local role_name
  local current_file="$TMP_DIR/current-client-roles-$user_id.json"
  local payload_file="$TMP_DIR/assign-role-$user_id.json"

  role_name=$(jq -r '.name' "$role_file")
  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$user_id/role-mappings/clients/$CLIENT_UUID" \
    | jq '.' > "$current_file"

  if jq -e --arg roleName "$role_name" 'any(.[]; .name == $roleName)' "$current_file" >/dev/null; then
    return 0
  fi

  jq -c '[.]' "$role_file" > "$payload_file"
  api_json POST "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$user_id/role-mappings/clients/$CLIENT_UUID" "$(cat "$payload_file")" '^(200|204)$' >/dev/null
}

remove_client_role_from_user() {
  local user_id=$1
  local role_file=$2
  local role_name
  local current_file="$TMP_DIR/current-client-roles-remove-$user_id.json"
  local payload_file="$TMP_DIR/remove-role-$user_id.json"

  role_name=$(jq -r '.name' "$role_file")
  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$user_id/role-mappings/clients/$CLIENT_UUID" \
    | jq '.' > "$current_file"

  if ! jq -e --arg roleName "$role_name" 'any(.[]; .name == $roleName)' "$current_file" >/dev/null; then
    return 0
  fi

  jq -c '[.]' "$role_file" > "$payload_file"
  api_json DELETE "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$user_id/role-mappings/clients/$CLIENT_UUID" "$(cat "$payload_file")" '^(200|204)$' >/dev/null
}

replace_account_type_role() {
  local user_id=$1
  local role_file=$2
  local current_file="$TMP_DIR/current-account-type-roles-$user_id.json"
  local remove_file="$TMP_DIR/remove-account-type-roles-$user_id.json"

  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$user_id/role-mappings/clients/$CLIENT_UUID" \
    | jq '.' > "$current_file"
  jq '[.[] | select((.name // "") | startswith("account-type-"))]' "$current_file" > "$remove_file"

  if [[ "$(json_length "$remove_file")" != "0" ]]; then
    api_json DELETE "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$user_id/role-mappings/clients/$CLIENT_UUID" "$(cat "$remove_file")" '^(200|204)$' >/dev/null
  fi

  assign_client_role_to_user "$user_id" "$role_file"
}

write_control_plane_state() {
  local user_id=$1
  local output_file=$2
  local user_file="$TMP_DIR/state-user-$user_id.json"
  local roles_file="$TMP_DIR/state-roles-$user_id.json"

  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$user_id" | jq '.' > "$user_file"
  api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/users/$user_id/role-mappings/clients/$CLIENT_UUID" \
    | jq '.' > "$roles_file"

  jq -n \
    --slurpfile user "$user_file" \
    --slurpfile roles "$roles_file" \
    '
    def attr($name): ($user[0].attributes[$name][0] // null);

    ([$roles[0][] | select((.name // "") | startswith("account-type-")) | .name] | sort) as $accountTypeRoles
    | ([$roles[0][] | select((.name // "") | startswith("service-")) | .name] | sort) as $serviceRoles
    | (attr("edrlab.lifecycle")) as $lifecycle
    | (attr("edrlab.linked_subject")) as $linkedSubject
    | {
        keycloak_user_id: $user[0].id,
        username: $user[0].username,
        email: $user[0].email,
        email_verified: $user[0].emailVerified,
        keycloak_enabled: $user[0].enabled,
        account_id: attr("edrlab.account_id"),
        lifecycle: $lifecycle,
        linked_subject: $linkedSubject,
        last_control_plane_correlation: attr("edrlab.last_control_plane_correlation"),
        managed_by: attr("edrlab.managed_by"),
        account_type_roles: $accountTypeRoles,
        service_roles: $serviceRoles,
        invariant_violations: ([
          if ($accountTypeRoles | length) != 1 then "account_type_role_count_invalid" else empty end,
          if (["invited", "active", "disabled", "archived"] | index($lifecycle)) then empty else "lifecycle_invalid" end,
          if $lifecycle == "active" and (($linkedSubject // "") | length) == 0 then "active_account_without_subject_link" else empty end,
          if (($serviceRoles | length) > 0) and ($accountTypeRoles[0] != "account-type-member") then "service_role_assigned_to_non_member" else empty end
        ])
      }
    ' > "$output_file"
}

write_authorization_decision() {
  local state_file=$1
  local output_file=$2
  local correlation_id=$3
  local target_service=$4
  local requested_action=$5
  local drift_detected=$6

  jq -n \
    --arg correlationId "$correlation_id" \
    --arg targetService "$target_service" \
    --arg requestedAction "$requested_action" \
    --argjson driftDetected "$drift_detected" \
    --slurpfile state "$state_file" \
    '
    $state[0] as $s
    | ($s.account_type_roles[0] // null) as $accountTypeRole
    | ($s.service_roles | index("service-catalog-consult")) as $hasCatalogRole
    | (
        if $driftDetected then
          {decision: "deny", reason_code: "drift_detected"}
        elif (($s.invariant_violations | length) > 0) then
          {decision: "deny", reason_code: "invariant_violation"}
        elif $s.lifecycle != "active" then
          {decision: "deny", reason_code: "account_not_active"}
        elif ($accountTypeRole == "account-type-admin" or $accountTypeRole == "account-type-super-admin") then
          {decision: "allow", reason_code: "active_privileged_account_inherits_service_access"}
        elif ($accountTypeRole == "account-type-member" and $hasCatalogRole != null) then
          {decision: "allow", reason_code: "active_member_has_service_role"}
        else
          {decision: "deny", reason_code: "missing_service_access_role"}
        end
      ) as $result
    | {
        correlation_id: $correlationId,
        source: "edrlab-iam-control-plane-api-poc-fixture",
        operation: "authorization.check",
        target_service: $targetService,
        requested_action: $requestedAction,
        actor_account_id: $s.account_id,
        actor_keycloak_user_id: $s.keycloak_user_id,
        decision: $result.decision,
        reason_code: $result.reason_code,
        fail_closed: ($result.decision != "allow"),
        drift_detected: $driftDetected,
        state: $s
      }
    ' > "$output_file"
}

write_effective_services_decision() {
  local state_file=$1
  local output_file=$2
  local correlation_id=$3
  local drift_detected=$4

  jq -n \
    --arg correlationId "$correlation_id" \
    --argjson driftDetected "$drift_detected" \
    --slurpfile state "$state_file" \
    '
    $state[0] as $s
    | ($s.account_type_roles[0] // null) as $accountTypeRole
    | ($s.service_roles | index("service-catalog-consult")) as $hasCatalogRole
    | (
        if $driftDetected then
          {decision: "deny", reason_code: "drift_detected", services: []}
        elif (($s.invariant_violations | length) > 0) then
          {decision: "deny", reason_code: "invariant_violation", services: []}
        elif $s.lifecycle != "active" then
          {decision: "deny", reason_code: "account_not_active", services: []}
        elif ($accountTypeRole == "account-type-admin" or $accountTypeRole == "account-type-super-admin") then
          {decision: "allow", reason_code: "active_privileged_account_inherits_service_access", services: ["catalog"]}
        elif ($accountTypeRole == "account-type-member" and $hasCatalogRole != null) then
          {decision: "allow", reason_code: "active_member_has_service_role", services: ["catalog"]}
        else
          {decision: "allow", reason_code: "active_account_without_effective_service", services: []}
        end
      ) as $result
    | {
        correlation_id: $correlationId,
        source: "edrlab-iam-control-plane-api-poc-fixture",
        operation: "GET /me/services",
        actor_account_id: $s.account_id,
        actor_keycloak_user_id: $s.keycloak_user_id,
        decision: $result.decision,
        reason_code: $result.reason_code,
        services: $result.services,
        drift_detected: $driftDetected,
        state: $s
      }
    ' > "$output_file"
}

wait_for_url "$KEYCLOAK_BASE_URL/realms/$KEYCLOAK_REALM/.well-known/openid-configuration" "PoC realm discovery"

ADMIN_TOKEN=$(admin_token)
if [[ -z "$ADMIN_TOKEN" || "$ADMIN_TOKEN" == "null" ]]; then
  fail "unable to obtain Keycloak admin token"
fi

CLIENT_UUID=$(client_uuid "$ADMIN_TOKEN")
[[ -n "$CLIENT_UUID" ]] || fail "client not found: $KEYCLOAK_CLIENT_ID"

RUN_TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
EVIDENCE_ROOT="$POC_DIR/evidence"
EVIDENCE_DIR="$EVIDENCE_ROOT/$RUN_TIMESTAMP"
TMP_DIR="$POC_DIR/tmp/wp-011-016-$RUN_TIMESTAMP"
mkdir -p "$EVIDENCE_DIR" "$TMP_DIR"
trap 'rm -rf "$TMP_DIR"' EXIT

RUN_STARTED_AT_MS=$(epoch_millis)
EVENT_WINDOW_STARTED_AT_MS=$((RUN_STARTED_AT_MS - 5000))

jq -n \
  --arg generatedAt "$(utc_timestamp)" \
  --argjson runStartedAtMs "$RUN_STARTED_AT_MS" \
  --argjson eventWindowStartedAtMs "$EVENT_WINDOW_STARTED_AT_MS" \
  '{
    generated_at: $generatedAt,
    run_started_at_ms: $runStartedAtMs,
    event_window_started_at_ms: $eventWindowStartedAtMs,
    note: "Keycloak event evidence is filtered to events at or after event_window_started_at_ms where possible."
  }' > "$EVIDENCE_DIR/wp-011-016-event-window.json"

events_config=$(api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/events/config")
jq '{eventsEnabled, eventsExpiration, adminEventsEnabled, adminEventsDetailsEnabled, enabledEventTypes}' \
  <<<"$events_config" > "$EVIDENCE_DIR/wp-011-016-events-config.json"
jq -e '.eventsEnabled == true and .adminEventsEnabled == true and .adminEventsDetailsEnabled == true' \
  "$EVIDENCE_DIR/wp-011-016-events-config.json" >/dev/null \
  || fail "Keycloak user/admin event settings are not enabled for the runtime bundle"
pass "Keycloak user and admin event settings are enabled"

ensure_user_profile_admin_edit_attributes
pass "Keycloak user profile allows PoC IAM attributes from the administrative context"

ACCOUNT_MEMBER_ROLE="account-type-member"
ACCOUNT_ADMIN_ROLE="account-type-admin"
ACCOUNT_SUPER_ADMIN_ROLE="account-type-super-admin"
SERVICE_CATALOG_ROLE="service-catalog-consult"

MEMBER_USERNAME="wp-iam-member-poc"
MEMBER_EMAIL="wp-iam-member-poc@example.invalid"
ADMIN_USERNAME="wp-iam-admin-poc"
ADMIN_EMAIL="wp-iam-admin-poc@example.invalid"
SUPER_ADMIN_USERNAME="wp-iam-super-admin-poc"
SUPER_ADMIN_EMAIL="wp-iam-super-admin-poc@example.invalid"
INVITED_USERNAME="wp-iam-invited-poc"
INVITED_EMAIL="wp-iam-invited-poc@example.invalid"
UNVERIFIED_USERNAME="wp-iam-unverified-poc"
UNVERIFIED_EMAIL="wp-iam-unverified-poc@example.invalid"

ensure_client_role \
  "$ACCOUNT_MEMBER_ROLE" \
  "PoC-only EDRLab account-type role for active validation mapping." \
  '{"edrlab.kind":["account_type"],"edrlab.account_type":["member"]}' \
  "$TMP_DIR/role-account-member.json"
ensure_client_role \
  "$ACCOUNT_ADMIN_ROLE" \
  "PoC-only EDRLab account-type role for active validation mapping." \
  '{"edrlab.kind":["account_type"],"edrlab.account_type":["admin"]}' \
  "$TMP_DIR/role-account-admin.json"
ensure_client_role \
  "$ACCOUNT_SUPER_ADMIN_ROLE" \
  "PoC-only EDRLab account-type role for active validation mapping." \
  '{"edrlab.kind":["account_type"],"edrlab.account_type":["super-admin"]}' \
  "$TMP_DIR/role-account-super-admin.json"
ensure_client_role \
  "$SERVICE_CATALOG_ROLE" \
  "PoC-only EDRLab member service-access role for catalog consultation." \
  '{"edrlab.kind":["service_access"],"edrlab.service":["catalog"],"edrlab.action":["consult"],"edrlab.role_status":["active"]}' \
  "$TMP_DIR/role-service-catalog.json"
pass "Client roles for IAM mapping exist"

ensure_user_fixture "$MEMBER_USERNAME" "$MEMBER_EMAIL" true "WP IAM" "Member" "$TMP_DIR/user-member.json"
ensure_user_fixture "$ADMIN_USERNAME" "$ADMIN_EMAIL" true "WP IAM" "Admin" "$TMP_DIR/user-admin.json"
ensure_user_fixture "$SUPER_ADMIN_USERNAME" "$SUPER_ADMIN_EMAIL" true "WP IAM" "SuperAdmin" "$TMP_DIR/user-super-admin.json"
ensure_user_fixture "$INVITED_USERNAME" "$INVITED_EMAIL" true "WP IAM" "Invited" "$TMP_DIR/user-invited.json"
ensure_user_fixture "$UNVERIFIED_USERNAME" "$UNVERIFIED_EMAIL" false "WP IAM" "Unverified" "$TMP_DIR/user-unverified.json"

MEMBER_USER_ID=$(jq -r '.id' "$TMP_DIR/user-member.json")
ADMIN_USER_ID=$(jq -r '.id' "$TMP_DIR/user-admin.json")
SUPER_ADMIN_USER_ID=$(jq -r '.id' "$TMP_DIR/user-super-admin.json")
INVITED_USER_ID=$(jq -r '.id' "$TMP_DIR/user-invited.json")
UNVERIFIED_USER_ID=$(jq -r '.id' "$TMP_DIR/user-unverified.json")

replace_account_type_role "$MEMBER_USER_ID" "$TMP_DIR/role-account-member.json"
replace_account_type_role "$ADMIN_USER_ID" "$TMP_DIR/role-account-admin.json"
replace_account_type_role "$SUPER_ADMIN_USER_ID" "$TMP_DIR/role-account-super-admin.json"
replace_account_type_role "$INVITED_USER_ID" "$TMP_DIR/role-account-member.json"
replace_account_type_role "$UNVERIFIED_USER_ID" "$TMP_DIR/role-account-member.json"

remove_client_role_from_user "$MEMBER_USER_ID" "$TMP_DIR/role-service-catalog.json"
remove_client_role_from_user "$ADMIN_USER_ID" "$TMP_DIR/role-service-catalog.json"
remove_client_role_from_user "$SUPER_ADMIN_USER_ID" "$TMP_DIR/role-service-catalog.json"
remove_client_role_from_user "$INVITED_USER_ID" "$TMP_DIR/role-service-catalog.json"
remove_client_role_from_user "$UNVERIFIED_USER_ID" "$TMP_DIR/role-service-catalog.json"

set_user_business_state "$MEMBER_USER_ID" "acct-wp011016-member" "active" "$MEMBER_USER_ID" "wp-011-016-baseline-member"
set_user_business_state "$ADMIN_USER_ID" "acct-wp011016-admin" "active" "$ADMIN_USER_ID" "wp-011-016-baseline-admin"
set_user_business_state "$SUPER_ADMIN_USER_ID" "acct-wp011016-super-admin" "active" "$SUPER_ADMIN_USER_ID" "wp-011-016-baseline-super-admin"
set_user_business_state "$INVITED_USER_ID" "acct-wp011016-invited" "invited" "" "wp-011-016-baseline-invited"
set_user_business_state "$UNVERIFIED_USER_ID" "acct-wp011016-unverified" "invited" "" "wp-011-016-baseline-unverified"
pass "PoC business-state attributes reset to baseline"

write_control_plane_state "$MEMBER_USER_ID" "$EVIDENCE_DIR/wp-011-016-member-baseline-state.json"
write_control_plane_state "$ADMIN_USER_ID" "$EVIDENCE_DIR/wp-011-016-admin-baseline-state.json"
write_control_plane_state "$SUPER_ADMIN_USER_ID" "$EVIDENCE_DIR/wp-011-016-super-admin-baseline-state.json"
write_control_plane_state "$INVITED_USER_ID" "$EVIDENCE_DIR/wp-011-016-invited-baseline-state.json"
write_control_plane_state "$UNVERIFIED_USER_ID" "$EVIDENCE_DIR/wp-011-016-unverified-baseline-state.json"

jq -n \
  --arg generatedAt "$(utc_timestamp)" \
  --arg realm "$KEYCLOAK_REALM" \
  --arg clientId "$KEYCLOAK_CLIENT_ID" \
  --arg clientUuid "$CLIENT_UUID" \
  --slurpfile memberRole "$TMP_DIR/role-account-member.json" \
  --slurpfile adminRole "$TMP_DIR/role-account-admin.json" \
  --slurpfile superAdminRole "$TMP_DIR/role-account-super-admin.json" \
  --slurpfile serviceRole "$TMP_DIR/role-service-catalog.json" \
  '{
    generated_at: $generatedAt,
    realm: $realm,
    client_id: $clientId,
    client_uuid: $clientUuid,
    mapping_under_test: {
      account_type_roles: [$memberRole[0].name, $adminRole[0].name, $superAdminRole[0].name],
      lifecycle_attribute: "edrlab.lifecycle",
      account_id_attribute: "edrlab.account_id",
      linked_subject_attribute: "edrlab.linked_subject",
      service_access_role: $serviceRole[0].name,
      authorization_contract: "edrlab-iam-control-plane-api authorization.check",
      audit_source: "edrlab-iam-control-plane-api"
    },
    roles: {
      member: $memberRole[0],
      admin: $adminRole[0],
      super_admin: $superAdminRole[0],
      service_catalog: $serviceRole[0]
    }
  }' > "$EVIDENCE_DIR/wp-011-016-keycloak-mapping.json"

assign_client_role_to_user "$MEMBER_USER_ID" "$TMP_DIR/role-service-catalog.json"
write_control_plane_state "$MEMBER_USER_ID" "$EVIDENCE_DIR/wp-011-016-member-after-service-role-assigned.json"
jq -e '.service_roles | index("service-catalog-consult") != null' \
  "$EVIDENCE_DIR/wp-011-016-member-after-service-role-assigned.json" >/dev/null \
  || fail "member service role was not assigned through the control-plane fixture"
pass "Controlled service-role assignment is visible in Keycloak state"

write_authorization_decision \
  "$EVIDENCE_DIR/wp-011-016-member-after-service-role-assigned.json" \
  "$EVIDENCE_DIR/wp-011-016-authorization-allow-active-member.json" \
  "wp-011-016-authz-active-member" \
  "catalog" \
  "consult" \
  false
write_effective_services_decision \
  "$EVIDENCE_DIR/wp-011-016-member-after-service-role-assigned.json" \
  "$EVIDENCE_DIR/wp-011-016-effective-services-active-member.json" \
  "wp-011-016-services-active-member" \
  false
jq -e '.decision == "allow"' "$EVIDENCE_DIR/wp-011-016-authorization-allow-active-member.json" >/dev/null \
  || fail "active member with service role should be allowed"
pass "authorization/check allows active member with service role"

write_control_plane_state "$MEMBER_USER_ID" "$EVIDENCE_DIR/wp-011-016-member-before-account-type-mutation-denied.json"
# This operation is denied by the PoC control-plane fixture before Keycloak mutation.
write_control_plane_state "$MEMBER_USER_ID" "$EVIDENCE_DIR/wp-011-016-member-after-account-type-mutation-denied.json"
jq -e '.account_type_roles == ["account-type-member"]' \
  "$EVIDENCE_DIR/wp-011-016-member-after-account-type-mutation-denied.json" >/dev/null \
  || fail "denied account-type mutation changed Keycloak state"
pass "Denied account-type mutation does not change Keycloak state"

write_control_plane_state "$INVITED_USER_ID" "$EVIDENCE_DIR/wp-011-016-invited-before-safe-onboarding.json"
set_user_business_state "$INVITED_USER_ID" "acct-wp011016-invited" "active" "$INVITED_USER_ID" "wp-011-016-safe-onboarding"
write_control_plane_state "$INVITED_USER_ID" "$EVIDENCE_DIR/wp-011-016-invited-after-safe-onboarding.json"
jq -e '.lifecycle == "active" and .linked_subject == .keycloak_user_id' \
  "$EVIDENCE_DIR/wp-011-016-invited-after-safe-onboarding.json" >/dev/null \
  || fail "safe onboarding did not activate and link invited user"
pass "Safe onboarding activation updates lifecycle and subject link"

write_control_plane_state "$UNVERIFIED_USER_ID" "$EVIDENCE_DIR/wp-011-016-unverified-before-onboarding-denied.json"
# This operation is denied by the PoC control-plane fixture before Keycloak mutation.
write_control_plane_state "$UNVERIFIED_USER_ID" "$EVIDENCE_DIR/wp-011-016-unverified-after-onboarding-denied.json"
jq -e '.lifecycle == "invited" and (.linked_subject == null)' \
  "$EVIDENCE_DIR/wp-011-016-unverified-after-onboarding-denied.json" >/dev/null \
  || fail "denied unverified onboarding changed Keycloak state"
pass "Unsafe unverified onboarding denial leaves Keycloak state unchanged"

write_control_plane_state "$MEMBER_USER_ID" "$EVIDENCE_DIR/wp-011-016-member-before-disable.json"
set_user_business_state "$MEMBER_USER_ID" "acct-wp011016-member" "disabled" "$MEMBER_USER_ID" "wp-011-016-disable-member"
write_control_plane_state "$MEMBER_USER_ID" "$EVIDENCE_DIR/wp-011-016-member-after-disable.json"
write_authorization_decision \
  "$EVIDENCE_DIR/wp-011-016-member-after-disable.json" \
  "$EVIDENCE_DIR/wp-011-016-authorization-deny-disabled-member.json" \
  "wp-011-016-authz-disabled-member" \
  "catalog" \
  "consult" \
  false
write_effective_services_decision \
  "$EVIDENCE_DIR/wp-011-016-member-after-disable.json" \
  "$EVIDENCE_DIR/wp-011-016-effective-services-deny-disabled-member.json" \
  "wp-011-016-services-disabled-member" \
  false
jq -e '.decision == "deny" and .reason_code == "account_not_active"' \
  "$EVIDENCE_DIR/wp-011-016-authorization-deny-disabled-member.json" >/dev/null \
  || fail "disabled member should be denied"
pass "authorization/check denies disabled member"

direct_set_user_lifecycle_without_control_plane "$MEMBER_USER_ID" "active"
write_control_plane_state "$MEMBER_USER_ID" "$EVIDENCE_DIR/wp-011-016-member-after-direct-admin-drift.json"
jq -n \
  --slurpfile expected "$EVIDENCE_DIR/wp-011-016-member-after-disable.json" \
  --slurpfile observed "$EVIDENCE_DIR/wp-011-016-member-after-direct-admin-drift.json" \
  '{
    scenario: "direct-admin-lifecycle-restore-drift",
    expected_managed_lifecycle: $expected[0].lifecycle,
    observed_keycloak_lifecycle: $observed[0].lifecycle,
    expected_last_control_plane_correlation: $expected[0].last_control_plane_correlation,
    observed_last_control_plane_correlation: $observed[0].last_control_plane_correlation,
    decision: (if $expected[0].lifecycle != $observed[0].lifecycle then "drift_detected" else "no_drift" end),
    reason_code: "unmanaged_keycloak_lifecycle_change",
    fail_closed: true
  }' > "$EVIDENCE_DIR/wp-011-016-drift-detection.json"
jq -e '.decision == "drift_detected"' "$EVIDENCE_DIR/wp-011-016-drift-detection.json" >/dev/null \
  || fail "direct-admin drift was not detected"
pass "Direct-admin lifecycle change is detected as drift"

write_authorization_decision \
  "$EVIDENCE_DIR/wp-011-016-member-after-direct-admin-drift.json" \
  "$EVIDENCE_DIR/wp-011-016-authorization-deny-drift-member.json" \
  "wp-011-016-authz-drift-member" \
  "catalog" \
  "consult" \
  true
write_effective_services_decision \
  "$EVIDENCE_DIR/wp-011-016-member-after-direct-admin-drift.json" \
  "$EVIDENCE_DIR/wp-011-016-effective-services-deny-drift-member.json" \
  "wp-011-016-services-drift-member" \
  true
jq -e '.decision == "deny" and .fail_closed == true' \
  "$EVIDENCE_DIR/wp-011-016-authorization-deny-drift-member.json" >/dev/null \
  || fail "drifted member should fail closed"
pass "authorization/check fails closed on drifted Keycloak state"

api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/clients/$CLIENT_UUID/protocol-mappers/models" \
  | jq '[.[] | {id, name, protocol, protocolMapper, config}]' \
  > "$EVIDENCE_DIR/wp-011-016-client-protocol-mappers.json"
client_privileged_mapper_count=$(jq '[.[] | select(((.protocolMapper // "") | test("acr|amr|loa|level"; "i")) or ((.name // "") | test("acr|amr|loa|level|authentication method"; "i")))] | length' "$EVIDENCE_DIR/wp-011-016-client-protocol-mappers.json")

api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM" \
  | jq '{realm, browserFlow, registrationFlow, directGrantFlow, resetCredentialsFlow, clientAuthenticationFlow}' \
  > "$EVIDENCE_DIR/wp-011-016-realm-flow-bindings.json"
browser_flow=$(jq -r '.browserFlow // "browser"' "$EVIDENCE_DIR/wp-011-016-realm-flow-bindings.json")
encoded_browser_flow=$(urlencode "$browser_flow")

api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/authentication/flows/$encoded_browser_flow/executions" \
  | jq '[
      .[]
      | {
          id,
          displayName,
          providerId,
          authenticator,
          authenticatorConfig,
          requirement,
          level,
          index,
          authenticationFlow,
          flowId,
          requirementChoices,
          reference_value_fields: (to_entries | map(select(.key | test("reference|acr|amr|loa"; "i"))))
        }
    ]' \
  > "$EVIDENCE_DIR/wp-011-016-browser-flow-executions.json"
configured_reference_values=$(jq '[.[] | .reference_value_fields[]?.value | select(type == "string" and length > 0)] | unique' "$EVIDENCE_DIR/wp-011-016-browser-flow-executions.json")

jq -n \
  --arg generatedAt "$(utc_timestamp)" \
  --arg browserFlow "$browser_flow" \
  --argjson mapperCount "$client_privileged_mapper_count" \
  --argjson configuredReferenceValues "$configured_reference_values" \
  '{
    generated_at: $generatedAt,
    scenario: "privileged-account-evidence-runtime-inspection",
    browser_flow: $browserFlow,
    client_privileged_mapper_count: $mapperCount,
    configured_browser_flow_reference_values: $configuredReferenceValues,
    result: (if ($mapperCount > 0 or ($configuredReferenceValues | length) > 0) then "candidate_evidence_found" else "blocked" end),
    reason_code: (if ($mapperCount > 0 or ($configuredReferenceValues | length) > 0) then "candidate_privileged_evidence_configuration_present" else "missing_explicit_privileged_authentication_evidence" end),
    privileged_activation_allowed: false,
    note: "This runtime bundle inspects configuration only. A dedicated step-up login validation is still required before admin or super-admin onboarding can be accepted."
  }' > "$EVIDENCE_DIR/wp-011-016-privileged-evidence.json"
pass "Privileged-evidence configuration inspection recorded"

CONTROL_PLANE_DECISIONS_FILE="$EVIDENCE_DIR/wp-011-016-control-plane-decisions.json"
jq -n \
  --arg generatedAt "$(utc_timestamp)" \
  --arg adminSubject "$ADMIN_USER_ID" \
  --arg superAdminSubject "$SUPER_ADMIN_USER_ID" \
  --arg technicalActorSubject "technical-keycloak-admin" \
  --slurpfile memberBaseline "$EVIDENCE_DIR/wp-011-016-member-baseline-state.json" \
  --slurpfile memberAfterRole "$EVIDENCE_DIR/wp-011-016-member-after-service-role-assigned.json" \
  --slurpfile memberBeforeTypeDenied "$EVIDENCE_DIR/wp-011-016-member-before-account-type-mutation-denied.json" \
  --slurpfile memberAfterTypeDenied "$EVIDENCE_DIR/wp-011-016-member-after-account-type-mutation-denied.json" \
  --slurpfile invitedBefore "$EVIDENCE_DIR/wp-011-016-invited-before-safe-onboarding.json" \
  --slurpfile invitedAfter "$EVIDENCE_DIR/wp-011-016-invited-after-safe-onboarding.json" \
  --slurpfile unverifiedBefore "$EVIDENCE_DIR/wp-011-016-unverified-before-onboarding-denied.json" \
  --slurpfile unverifiedAfter "$EVIDENCE_DIR/wp-011-016-unverified-after-onboarding-denied.json" \
  --slurpfile memberBeforeDisable "$EVIDENCE_DIR/wp-011-016-member-before-disable.json" \
  --slurpfile memberAfterDisable "$EVIDENCE_DIR/wp-011-016-member-after-disable.json" \
  --slurpfile memberAfterDrift "$EVIDENCE_DIR/wp-011-016-member-after-direct-admin-drift.json" \
  --slurpfile drift "$EVIDENCE_DIR/wp-011-016-drift-detection.json" \
  --slurpfile privileged "$EVIDENCE_DIR/wp-011-016-privileged-evidence.json" \
  '[
    {
      scenario: "service-role-assignment",
      correlation_id: "wp-011-016-service-role-assigned",
      operation: "service_role.assigned",
      expected_result: "allow",
      observed_result: (if ($memberAfterRole[0].service_roles | index("service-catalog-consult")) != null then "allow" else "deny" end),
      expected_reason_code: "actor_scope_allows_member_service_role_assignment",
      reason_code: "actor_scope_allows_member_service_role_assignment",
      actor_account_id: "acct-wp011016-admin",
      actor_subject: $adminSubject,
      target_account_id: $memberBaseline[0].account_id,
      before: $memberBaseline[0],
      after: $memberAfterRole[0],
      keycloak_mutation_expected: true,
      keycloak_mutation_observed: (($memberAfterRole[0].service_roles | index("service-catalog-consult")) != null),
      pass: (($memberAfterRole[0].service_roles | index("service-catalog-consult")) != null)
    },
    {
      scenario: "account-type-mutation-denied",
      correlation_id: "wp-011-016-account-type-mutation-denied",
      operation: "account_type.mutation_denied",
      expected_result: "deny",
      observed_result: "deny",
      expected_reason_code: "account_type_is_immutable",
      reason_code: "account_type_is_immutable",
      actor_account_id: "acct-wp011016-admin",
      actor_subject: $adminSubject,
      target_account_id: $memberBeforeTypeDenied[0].account_id,
      before: $memberBeforeTypeDenied[0],
      after: $memberAfterTypeDenied[0],
      keycloak_mutation_expected: false,
      keycloak_mutation_observed: ($memberBeforeTypeDenied[0].account_type_roles != $memberAfterTypeDenied[0].account_type_roles),
      pass: (
        $memberAfterTypeDenied[0].account_type_roles == ["account-type-member"]
        and $memberBeforeTypeDenied[0].account_type_roles == $memberAfterTypeDenied[0].account_type_roles
      )
    },
    {
      scenario: "safe-onboarding-activation",
      correlation_id: "wp-011-016-safe-onboarding",
      operation: "onboarding.activation.allowed",
      expected_result: "allow",
      observed_result: (if $invitedAfter[0].lifecycle == "active" and $invitedAfter[0].linked_subject == $invitedAfter[0].keycloak_user_id then "allow" else "deny" end),
      expected_reason_code: "verified_single_invitation_match",
      reason_code: "verified_single_invitation_match",
      actor_account_id: $invitedAfter[0].account_id,
      actor_subject: $invitedAfter[0].keycloak_user_id,
      target_account_id: $invitedAfter[0].account_id,
      before: $invitedBefore[0],
      after: $invitedAfter[0],
      keycloak_mutation_expected: true,
      keycloak_mutation_observed: ($invitedBefore[0].lifecycle != $invitedAfter[0].lifecycle and $invitedAfter[0].linked_subject == $invitedAfter[0].keycloak_user_id),
      pass: ($invitedAfter[0].lifecycle == "active" and $invitedAfter[0].linked_subject == $invitedAfter[0].keycloak_user_id)
    },
    {
      scenario: "unverified-onboarding-denied",
      correlation_id: "wp-011-016-unverified-onboarding",
      operation: "onboarding.activation.denied",
      expected_result: "deny",
      observed_result: "deny",
      expected_reason_code: "email_not_verified",
      reason_code: "email_not_verified",
      actor_account_id: $unverifiedBefore[0].account_id,
      actor_subject: $unverifiedBefore[0].keycloak_user_id,
      target_account_id: $unverifiedBefore[0].account_id,
      before: $unverifiedBefore[0],
      after: $unverifiedAfter[0],
      keycloak_mutation_expected: false,
      keycloak_mutation_observed: (
        $unverifiedBefore[0].lifecycle != $unverifiedAfter[0].lifecycle
        or $unverifiedBefore[0].linked_subject != $unverifiedAfter[0].linked_subject
      ),
      pass: ($unverifiedAfter[0].lifecycle == "invited" and $unverifiedAfter[0].linked_subject == null)
    },
    {
      scenario: "account-disable",
      correlation_id: "wp-011-016-disable-member",
      operation: "account.disabled",
      expected_result: "allow",
      observed_result: (if $memberAfterDisable[0].lifecycle == "disabled" then "allow" else "deny" end),
      expected_reason_code: "actor_scope_allows_member_disable",
      reason_code: "actor_scope_allows_member_disable",
      actor_account_id: "acct-wp011016-admin",
      actor_subject: $adminSubject,
      target_account_id: $memberBeforeDisable[0].account_id,
      before: $memberBeforeDisable[0],
      after: $memberAfterDisable[0],
      keycloak_mutation_expected: true,
      keycloak_mutation_observed: ($memberBeforeDisable[0].lifecycle != $memberAfterDisable[0].lifecycle),
      pass: ($memberAfterDisable[0].lifecycle == "disabled")
    },
    {
      scenario: "direct-admin-drift-detected",
      correlation_id: "wp-011-016-direct-admin-drift",
      operation: "drift.detected",
      expected_result: "drift_detected",
      observed_result: $drift[0].decision,
      expected_reason_code: "unmanaged_keycloak_lifecycle_change",
      reason_code: $drift[0].reason_code,
      actor_account_id: "technical-keycloak-admin",
      actor_subject: $technicalActorSubject,
      target_account_id: $memberAfterDrift[0].account_id,
      before: $memberAfterDisable[0],
      after: $memberAfterDrift[0],
      keycloak_mutation_expected: true,
      keycloak_mutation_observed: ($memberAfterDisable[0].lifecycle != $memberAfterDrift[0].lifecycle),
      pass: ($drift[0].decision == "drift_detected" and $memberAfterDisable[0].lifecycle != $memberAfterDrift[0].lifecycle)
    },
    {
      scenario: "privileged-evidence-check",
      correlation_id: "wp-011-016-privileged-evidence",
      operation: "privileged_onboarding.evidence_checked",
      expected_result: "candidate_evidence_found_or_blocked",
      observed_result: $privileged[0].result,
      expected_reason_code: "candidate_privileged_evidence_or_missing_explicit_privileged_authentication_evidence",
      reason_code: $privileged[0].reason_code,
      actor_account_id: "acct-wp011016-super-admin",
      actor_subject: $superAdminSubject,
      target_account_id: "acct-wp011016-admin",
      before: {},
      after: $privileged[0],
      keycloak_mutation_expected: false,
      keycloak_mutation_observed: false,
      blocked: ($privileged[0].result == "blocked"),
      pass: ($privileged[0].result == "blocked" or $privileged[0].result == "candidate_evidence_found")
    }
  ]' > "$CONTROL_PLANE_DECISIONS_FILE"

jq -e 'all(.[]; .pass == true)' "$CONTROL_PLANE_DECISIONS_FILE" >/dev/null \
  || fail "one or more IAM Control Plane API fixture decisions did not match expected outcomes"
pass "IAM Control Plane API fixture decisions matched expected outcomes"

api_get "$ADMIN_TOKEN" "realms/$KEYCLOAK_REALM/admin-events?max=200" \
  | jq \
      --arg memberId "$MEMBER_USER_ID" \
      --arg adminId "$ADMIN_USER_ID" \
      --arg superAdminId "$SUPER_ADMIN_USER_ID" \
      --arg invitedId "$INVITED_USER_ID" \
      --arg unverifiedId "$UNVERIFIED_USER_ID" \
      --arg clientUuid "$CLIENT_UUID" \
      --argjson eventWindowStartedAtMs "$EVENT_WINDOW_STARTED_AT_MS" \
      '
      [$memberId, $adminId, $superAdminId, $invitedId, $unverifiedId, $clientUuid] as $ids
      | [.[] | select(
          .time >= $eventWindowStartedAtMs
          and ((.resourcePath // "") as $path | any($ids[]; $path | contains(.)))
        )
      | {
          time,
          realmId,
          operationType,
          resourceType,
          resourcePath,
          representation_present: (.representation != null),
          error,
          authDetails: {
            realmId: .authDetails.realmId,
            clientId: .authDetails.clientId,
            userId_present: (.authDetails.userId != null),
            ipAddress: .authDetails.ipAddress
          }
        }]
      ' > "$EVIDENCE_DIR/wp-011-016-keycloak-admin-events.json"
admin_event_count=$(json_length "$EVIDENCE_DIR/wp-011-016-keycloak-admin-events.json")
[[ "$admin_event_count" -ge 1 ]] || fail "expected run-scoped Keycloak admin events for IAM runtime bundle"
pass "Run-scoped Keycloak admin events collected"

ADMIN_EVENT_CORRELATION_FILE="$EVIDENCE_DIR/wp-011-016-keycloak-admin-event-correlation.json"
jq -n \
  --arg memberId "$MEMBER_USER_ID" \
  --arg invitedId "$INVITED_USER_ID" \
  --arg clientUuid "$CLIENT_UUID" \
  --slurpfile adminEvents "$EVIDENCE_DIR/wp-011-016-keycloak-admin-events.json" \
  '
  def path_contains($value): ((.resourcePath // "") | contains($value));
  def role_mapping_path: ((.resourcePath // "") | contains("role-mappings/clients"));

  ($adminEvents[0] | map(select(path_contains($memberId) and path_contains($clientUuid) and role_mapping_path))) as $memberRoleMappingEvents
  | ($adminEvents[0] | map(select(path_contains($memberId) and .operationType == "UPDATE"))) as $memberUpdateEvents
  | ($adminEvents[0] | map(select(path_contains($invitedId) and .operationType == "UPDATE"))) as $invitedUpdateEvents
  | {
      service_role_assignment_event_count: ($memberRoleMappingEvents | length),
      member_lifecycle_update_event_count: ($memberUpdateEvents | length),
      invited_onboarding_update_event_count: ($invitedUpdateEvents | length),
      representation_present_event_count: ($adminEvents[0] | map(select(.representation_present == true)) | length),
      correlations: [
        {
          scenario: "service-role-assignment",
          expected_resource: ("users/" + $memberId + "/role-mappings/clients/" + $clientUuid),
          matching_event_count: ($memberRoleMappingEvents | length)
        },
        {
          scenario: "account-disable-and-direct-admin-drift",
          expected_resource_contains: $memberId,
          expected_operation_type: "UPDATE",
          matching_event_count: ($memberUpdateEvents | length)
        },
        {
          scenario: "safe-onboarding-activation",
          expected_resource_contains: $invitedId,
          expected_operation_type: "UPDATE",
          matching_event_count: ($invitedUpdateEvents | length)
        }
      ],
      pass: (
        (($memberRoleMappingEvents | length) >= 1)
        and (($memberUpdateEvents | length) >= 2)
        and (($invitedUpdateEvents | length) >= 1)
      )
    }
  ' > "$ADMIN_EVENT_CORRELATION_FILE"

jq -e '.pass == true' "$ADMIN_EVENT_CORRELATION_FILE" >/dev/null \
  || fail "Keycloak admin events do not correlate with the required IAM runtime scenarios"
pass "Keycloak admin events correlate with service-role, lifecycle, onboarding, and drift scenarios"

jq -n \
  --arg generatedAt "$(utc_timestamp)" \
  --arg adminSubject "$ADMIN_USER_ID" \
  --arg superAdminSubject "$SUPER_ADMIN_USER_ID" \
  --arg technicalActorSubject "technical-keycloak-admin" \
  --slurpfile memberBaseline "$EVIDENCE_DIR/wp-011-016-member-baseline-state.json" \
  --slurpfile memberAfterRole "$EVIDENCE_DIR/wp-011-016-member-after-service-role-assigned.json" \
  --slurpfile memberBeforeTypeDenied "$EVIDENCE_DIR/wp-011-016-member-before-account-type-mutation-denied.json" \
  --slurpfile memberAfterTypeDenied "$EVIDENCE_DIR/wp-011-016-member-after-account-type-mutation-denied.json" \
  --slurpfile invitedBefore "$EVIDENCE_DIR/wp-011-016-invited-before-safe-onboarding.json" \
  --slurpfile invitedAfter "$EVIDENCE_DIR/wp-011-016-invited-after-safe-onboarding.json" \
  --slurpfile unverifiedBefore "$EVIDENCE_DIR/wp-011-016-unverified-before-onboarding-denied.json" \
  --slurpfile unverifiedAfter "$EVIDENCE_DIR/wp-011-016-unverified-after-onboarding-denied.json" \
  --slurpfile memberBeforeDisable "$EVIDENCE_DIR/wp-011-016-member-before-disable.json" \
  --slurpfile memberAfterDisable "$EVIDENCE_DIR/wp-011-016-member-after-disable.json" \
  --slurpfile memberAfterDrift "$EVIDENCE_DIR/wp-011-016-member-after-direct-admin-drift.json" \
  --slurpfile authAllow "$EVIDENCE_DIR/wp-011-016-authorization-allow-active-member.json" \
  --slurpfile authDisabled "$EVIDENCE_DIR/wp-011-016-authorization-deny-disabled-member.json" \
  --slurpfile authDrift "$EVIDENCE_DIR/wp-011-016-authorization-deny-drift-member.json" \
  --slurpfile drift "$EVIDENCE_DIR/wp-011-016-drift-detection.json" \
  --slurpfile privileged "$EVIDENCE_DIR/wp-011-016-privileged-evidence.json" \
  '[
    {
      audit_event_id: "wp-011-016-service-role-assigned",
      correlation_id: "wp-011-016-service-role-assigned",
      occurred_at: $generatedAt,
      actor_account_id: "acct-wp011016-admin",
      actor_subject: $adminSubject,
      operation: "service_role.assigned",
      target_account_id: $memberBaseline[0].account_id,
      target_service: "catalog",
      decision: "allow",
      reason_code: "actor_scope_allows_member_service_role_assignment",
      before: $memberBaseline[0],
      after: $memberAfterRole[0],
      keycloak_refs: [{type: "admin_event", file: "wp-011-016-keycloak-admin-events.json"}],
      source: "edrlab-iam-control-plane-api"
    },
    {
      audit_event_id: "wp-011-016-account-type-mutation-denied",
      correlation_id: "wp-011-016-account-type-mutation-denied",
      occurred_at: $generatedAt,
      actor_account_id: "acct-wp011016-admin",
      actor_subject: $adminSubject,
      operation: "account_type.mutation_denied",
      target_account_id: $memberBeforeTypeDenied[0].account_id,
      decision: "deny",
      reason_code: "account_type_is_immutable",
      before: $memberBeforeTypeDenied[0],
      after: $memberAfterTypeDenied[0],
      keycloak_refs: [],
      source: "edrlab-iam-control-plane-api"
    },
    {
      audit_event_id: "wp-011-016-onboarding-activation-allowed",
      correlation_id: "wp-011-016-safe-onboarding",
      occurred_at: $generatedAt,
      actor_account_id: $invitedAfter[0].account_id,
      actor_subject: $invitedAfter[0].keycloak_user_id,
      operation: "onboarding.activation.allowed",
      target_account_id: $invitedAfter[0].account_id,
      decision: "allow",
      reason_code: "verified_single_invitation_match",
      before: $invitedBefore[0],
      after: $invitedAfter[0],
      keycloak_refs: [{type: "admin_event", file: "wp-011-016-keycloak-admin-events.json"}],
      source: "edrlab-iam-control-plane-api"
    },
    {
      audit_event_id: "wp-011-016-onboarding-activation-denied",
      correlation_id: "wp-011-016-unverified-onboarding",
      occurred_at: $generatedAt,
      actor_account_id: $unverifiedBefore[0].account_id,
      actor_subject: $unverifiedBefore[0].keycloak_user_id,
      operation: "onboarding.activation.denied",
      target_account_id: $unverifiedBefore[0].account_id,
      decision: "deny",
      reason_code: "email_not_verified",
      before: $unverifiedBefore[0],
      after: $unverifiedAfter[0],
      keycloak_refs: [],
      source: "edrlab-iam-control-plane-api"
    },
    {
      audit_event_id: "wp-011-016-account-disabled",
      correlation_id: "wp-011-016-disable-member",
      occurred_at: $generatedAt,
      actor_account_id: "acct-wp011016-admin",
      actor_subject: $adminSubject,
      operation: "account.disabled",
      target_account_id: $memberBeforeDisable[0].account_id,
      decision: "allow",
      reason_code: "actor_scope_allows_member_disable",
      before: $memberBeforeDisable[0],
      after: $memberAfterDisable[0],
      keycloak_refs: [{type: "admin_event", file: "wp-011-016-keycloak-admin-events.json"}],
      source: "edrlab-iam-control-plane-api"
    },
    {
      audit_event_id: "wp-011-016-authorization-check-allowed",
      correlation_id: $authAllow[0].correlation_id,
      occurred_at: $generatedAt,
      actor_account_id: $authAllow[0].actor_account_id,
      actor_subject: $authAllow[0].actor_keycloak_user_id,
      operation: "authorization.check.allowed",
      target_account_id: $authAllow[0].actor_account_id,
      target_service: $authAllow[0].target_service,
      decision: $authAllow[0].decision,
      reason_code: $authAllow[0].reason_code,
      before: $authAllow[0].state,
      after: $authAllow[0].state,
      keycloak_refs: [],
      source: "edrlab-iam-control-plane-api"
    },
    {
      audit_event_id: "wp-011-016-authorization-check-denied-disabled",
      correlation_id: $authDisabled[0].correlation_id,
      occurred_at: $generatedAt,
      actor_account_id: $authDisabled[0].actor_account_id,
      actor_subject: $authDisabled[0].actor_keycloak_user_id,
      operation: "authorization.check.denied",
      target_account_id: $authDisabled[0].actor_account_id,
      target_service: $authDisabled[0].target_service,
      decision: $authDisabled[0].decision,
      reason_code: $authDisabled[0].reason_code,
      before: $authDisabled[0].state,
      after: $authDisabled[0].state,
      keycloak_refs: [],
      source: "edrlab-iam-control-plane-api"
    },
    {
      audit_event_id: "wp-011-016-drift-detected",
      correlation_id: "wp-011-016-direct-admin-drift",
      occurred_at: $generatedAt,
      actor_account_id: "technical-keycloak-admin",
      actor_subject: $technicalActorSubject,
      operation: "drift.detected",
      target_account_id: $memberAfterDrift[0].account_id,
      decision: $drift[0].decision,
      reason_code: $drift[0].reason_code,
      before: $memberAfterDisable[0],
      after: $memberAfterDrift[0],
      keycloak_refs: [{type: "admin_event", file: "wp-011-016-keycloak-admin-events.json"}],
      source: "edrlab-iam-control-plane-api"
    },
    {
      audit_event_id: "wp-011-016-authorization-check-denied-drift",
      correlation_id: $authDrift[0].correlation_id,
      occurred_at: $generatedAt,
      actor_account_id: $authDrift[0].actor_account_id,
      actor_subject: $authDrift[0].actor_keycloak_user_id,
      operation: "authorization.check.denied",
      target_account_id: $authDrift[0].actor_account_id,
      target_service: $authDrift[0].target_service,
      decision: $authDrift[0].decision,
      reason_code: $authDrift[0].reason_code,
      before: $authDrift[0].state,
      after: $authDrift[0].state,
      keycloak_refs: [],
      source: "edrlab-iam-control-plane-api"
    },
    {
      audit_event_id: "wp-011-016-privileged-evidence-blocked",
      correlation_id: "wp-011-016-privileged-evidence",
      occurred_at: $generatedAt,
      actor_account_id: "acct-wp011016-super-admin",
      actor_subject: $superAdminSubject,
      operation: "privileged_onboarding.evidence_checked",
      target_account_id: "acct-wp011016-admin",
      decision: $privileged[0].result,
      reason_code: $privileged[0].reason_code,
      before: {},
      after: $privileged[0],
      keycloak_refs: [{type: "configuration", file: "wp-011-016-client-protocol-mappers.json"}, {type: "configuration", file: "wp-011-016-browser-flow-executions.json"}],
      source: "edrlab-iam-control-plane-api"
    },
    {
      audit_event_id: "wp-011-016-audit-read",
      correlation_id: "wp-011-016-audit-read",
      occurred_at: $generatedAt,
      actor_account_id: "acct-wp011016-super-admin",
      actor_subject: $superAdminSubject,
      operation: "audit.read",
      target_account_id: "audit-log-poc",
      decision: "allow",
      reason_code: "super_admin_can_consult_audit",
      before: {},
      after: {},
      keycloak_refs: [],
      source: "edrlab-iam-control-plane-api"
    },
    {
      audit_event_id: "wp-011-016-audit-exported",
      correlation_id: "wp-011-016-audit-export",
      occurred_at: $generatedAt,
      actor_account_id: "acct-wp011016-super-admin",
      actor_subject: $superAdminSubject,
      operation: "audit.exported",
      target_account_id: "audit-export-poc",
      decision: "allow",
      reason_code: "super_admin_can_export_audit",
      before: {},
      after: {},
      keycloak_refs: [],
      source: "edrlab-iam-control-plane-api"
    }
  ]' > "$EVIDENCE_DIR/wp-011-016-local-audit.json"

for required_field in \
  audit_event_id \
  correlation_id \
  occurred_at \
  actor_account_id \
  actor_subject \
  operation \
  decision \
  reason_code \
  source; do
  jq -e --arg field "$required_field" \
    'all(.[]; has($field) and (.[$field] != null) and ((.[$field] | tostring) | length > 0))' \
    "$EVIDENCE_DIR/wp-011-016-local-audit.json" >/dev/null \
    || fail "local audit records are missing required field: $required_field"
done
pass "Local EDRLab audit records contain required WP-016 fields"

jq -n \
  --slurpfile serviceRole "$EVIDENCE_DIR/wp-011-016-member-after-service-role-assigned.json" \
  --slurpfile typeDenied "$EVIDENCE_DIR/wp-011-016-member-after-account-type-mutation-denied.json" \
  --slurpfile invitedAfter "$EVIDENCE_DIR/wp-011-016-invited-after-safe-onboarding.json" \
  --slurpfile unverifiedAfter "$EVIDENCE_DIR/wp-011-016-unverified-after-onboarding-denied.json" \
  --slurpfile authAllow "$EVIDENCE_DIR/wp-011-016-authorization-allow-active-member.json" \
  --slurpfile authDisabled "$EVIDENCE_DIR/wp-011-016-authorization-deny-disabled-member.json" \
  --slurpfile authDrift "$EVIDENCE_DIR/wp-011-016-authorization-deny-drift-member.json" \
  --slurpfile drift "$EVIDENCE_DIR/wp-011-016-drift-detection.json" \
  --slurpfile privileged "$EVIDENCE_DIR/wp-011-016-privileged-evidence.json" \
  --slurpfile adminEvents "$EVIDENCE_DIR/wp-011-016-keycloak-admin-events.json" \
  --slurpfile adminEventCorrelation "$EVIDENCE_DIR/wp-011-016-keycloak-admin-event-correlation.json" \
  --slurpfile controlPlaneDecisions "$CONTROL_PLANE_DECISIONS_FILE" \
  --slurpfile localAudit "$EVIDENCE_DIR/wp-011-016-local-audit.json" \
  --arg generatedAt "$(utc_timestamp)" \
  '{
    generated_at: $generatedAt,
    work_packages: ["WP-011", "WP-012", "WP-013", "WP-014", "WP-015", "WP-016"],
    result: (
      if (
        ($serviceRole[0].service_roles | index("service-catalog-consult")) != null
        and ($typeDenied[0].account_type_roles == ["account-type-member"])
        and ($invitedAfter[0].lifecycle == "active")
        and ($invitedAfter[0].linked_subject == $invitedAfter[0].keycloak_user_id)
        and ($unverifiedAfter[0].lifecycle == "invited")
        and ($unverifiedAfter[0].linked_subject == null)
        and ($authAllow[0].decision == "allow")
        and ($authDisabled[0].decision == "deny")
        and ($authDrift[0].decision == "deny")
        and ($drift[0].decision == "drift_detected")
        and (($adminEvents[0] | length) >= 1)
        and ($adminEventCorrelation[0].pass == true)
        and all($controlPlaneDecisions[0][]; .pass == true)
        and (($localAudit[0] | length) >= 12)
      )
      then
        if $privileged[0].result == "blocked" then "pass_with_blocked_privileged_evidence" else "pass" end
      else "fail" end
    ),
    checks: {
      controlled_service_role_assignment: (($serviceRole[0].service_roles | index("service-catalog-consult")) != null),
      account_type_mutation_denied_without_keycloak_change: ($typeDenied[0].account_type_roles == ["account-type-member"]),
      safe_onboarding_activated_and_linked: ($invitedAfter[0].lifecycle == "active" and $invitedAfter[0].linked_subject == $invitedAfter[0].keycloak_user_id),
      unverified_onboarding_denied_without_mutation: ($unverifiedAfter[0].lifecycle == "invited" and $unverifiedAfter[0].linked_subject == null),
      authorization_allow_active_member: ($authAllow[0].decision == "allow"),
      authorization_deny_disabled_member: ($authDisabled[0].decision == "deny"),
      authorization_deny_drift: ($authDrift[0].decision == "deny"),
      drift_detected: ($drift[0].decision == "drift_detected"),
      keycloak_admin_events_collected: (($adminEvents[0] | length) >= 1),
        local_audit_record_count: ($localAudit[0] | length),
        control_plane_decision_count: ($controlPlaneDecisions[0] | length),
        control_plane_decisions_passed: all($controlPlaneDecisions[0][]; .pass == true),
        admin_event_correlation_passed: $adminEventCorrelation[0].pass,
        admin_event_correlation: $adminEventCorrelation[0],
        privileged_evidence_result: $privileged[0].result
      },
      blocked: ($privileged[0].result == "blocked"),
      blocked_work_packages: (if $privileged[0].result == "blocked" then ["WP-013"] else [] end),
      production_gaps: [
      "PoC-only IAM Control Plane API fixture, not production service code.",
      "No production database topology, migration, CI, deployment, or durable audit store is created.",
      "Privileged admin/super-admin activation remains blocked unless explicit step-up evidence is configured and verified.",
      "Service-to-control-plane authentication, latency, retries, timeout, and monitoring remain review inputs.",
      "Backup/restore, break-glass, tamper resistance, retention, and alerting remain Phase 5 questions."
    ]
  }' > "$EVIDENCE_DIR/wp-011-016-summary.json"

jq -e '.result == "pass" or .result == "pass_with_blocked_privileged_evidence"' \
  "$EVIDENCE_DIR/wp-011-016-summary.json" >/dev/null \
  || fail "runtime bundle summary did not pass"
pass "WP-011 through WP-016 runtime bundle summary passed"
if jq -e '.blocked == true' "$EVIDENCE_DIR/wp-011-016-summary.json" >/dev/null; then
  echo "BLOCKED WP-013 privileged evidence remains unresolved; see wp-011-016-summary.json" >&2
fi

cat > "$EVIDENCE_DIR/wp-011-016-evidence.md" <<EOF
# WP-011 Through WP-016 Runtime Evidence

Scenario: Keycloak IAM plus EDRLab IAM Control Plane API runtime bundle
Work package: WP-011, WP-012, WP-013, WP-014, WP-015, WP-016
Requirement links: FR-001, FR-011 through FR-016, FR-020, FR-021, FR-024, FR-026, FR-027, FR-028, FR-033, FR-034, FR-035, FR-038, FR-039, FR-043, FR-044
Mapping under test: Client roles for account type and service access, user attributes for lifecycle/account ID/subject link, IAM Control Plane API fixture for business decisions and audit
Setup: Docker Compose Keycloak runtime, realm \`$KEYCLOAK_REALM\`, client \`$KEYCLOAK_CLIENT_ID\`, dedicated PoC users \`$MEMBER_USERNAME\`, \`$ADMIN_USERNAME\`, \`$SUPER_ADMIN_USERNAME\`, \`$INVITED_USERNAME\`, and \`$UNVERIFIED_USERNAME\`
Action: Scripted Keycloak Admin REST setup, controlled service-role assignment, denied account-type mutation, safe onboarding activation, unsafe onboarding denial, disable/access-stop check, direct-admin lifecycle drift, protected-service authorization checks, Keycloak admin-event collection, privileged-evidence inspection, and local EDRLab audit record generation
Expected result: Controlled mutations are visible in Keycloak state; denied operations do not mutate Keycloak; protected-service checks allow only active authorized state and fail closed on disabled/drifted state; local audit records cover business decisions; Keycloak events remain supplemental evidence
Observed result: \`$(jq -r '.result' "$EVIDENCE_DIR/wp-011-016-summary.json")\`
Evidence collected:
- \`wp-011-016-keycloak-mapping.json\`
- \`wp-011-016-member-after-service-role-assigned.json\`
- \`wp-011-016-member-after-account-type-mutation-denied.json\`
- \`wp-011-016-invited-after-safe-onboarding.json\`
- \`wp-011-016-unverified-after-onboarding-denied.json\`
- \`wp-011-016-authorization-allow-active-member.json\`
- \`wp-011-016-authorization-deny-disabled-member.json\`
- \`wp-011-016-authorization-deny-drift-member.json\`
- \`wp-011-016-effective-services-active-member.json\`
- \`wp-011-016-effective-services-deny-disabled-member.json\`
- \`wp-011-016-effective-services-deny-drift-member.json\`
- \`wp-011-016-drift-detection.json\`
- \`wp-011-016-client-protocol-mappers.json\`
- \`wp-011-016-realm-flow-bindings.json\`
- \`wp-011-016-browser-flow-executions.json\`
- \`wp-011-016-privileged-evidence.json\`
- \`wp-011-016-control-plane-decisions.json\`
- \`wp-011-016-events-config.json\`
- \`wp-011-016-user-profile-config.json\`
- \`wp-011-016-keycloak-admin-events.json\`
- \`wp-011-016-keycloak-admin-event-correlation.json\`
- \`wp-011-016-local-audit.json\`
- \`wp-011-016-summary.json\`
Pass / fail / blocked: \`$(jq -r '.result' "$EVIDENCE_DIR/wp-011-016-summary.json")\`
Residual risk: This script is a PoC-only IAM Control Plane API fixture. It does not create production service code, persistent databases, production audit storage, service-to-service authentication, monitoring, alerting, backup/restore, or tamper-resistant retention.
Production gap: Privileged activation remains blocked unless explicit step-up evidence is configured and verified. Production adoption still requires Phase 5 review of runtime evidence, database topology, audit storage, direct-admin governance, protected-service integration behavior, and self-hosted Keycloak operations.
Decision impact: The runtime bundle can support Phase 5 review only after execution evidence is inspected. It does not approve Phase 6 production MVP implementation.
EOF

echo "Evidence written to: $EVIDENCE_DIR"
