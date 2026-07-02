# Docker Ansible VPS Lab

This lab tests the Ansible deployment from an Ansible control container against
a minimal Debian SSH target container on a dedicated Docker bridge IP address.

It is useful for catching clean-host provisioning issues before using a real
VPS. It is not a perfect production substitute: the target is still a container,
and full runtime deployment requires privileged Docker-in-Docker support from
the local Docker host.

## Shape

- `ansible-control`: Debian-based control container with Ansible, SSH, sshpass,
  rsync, and the repository mounted at `/work`.
- `debian-vps`: Debian 12 target with SSH enabled, reachable at
  `172.28.47.10` on the lab bridge network.
- Caddy reverse proxy with internal TLS for `lab-auth.localhost`,
  `lab-iam.localhost`, and `lab-demo.localhost`.
- Initial target SSH: `root` / `root`, for disposable lab use only.
- The lab generates a throwaway SSH key in the `ansible-lab-runtime` Docker
  volume, provisions the `deploy` user, then verifies key-only login as
  `deploy`.

## Run

From this directory:

```bash
docker compose build
docker compose up -d debian-vps
docker compose run --rm ansible-control
```

The default run executes:

1. Ansible collection install.
2. Syntax checks for `provision.yml` and `deploy-access-control.yml`.
3. Debian provisioning against the target over SSH as `root`.
4. SSH verification as the managed `deploy` user.

To attempt the full access-control runtime deployment inside the target
container as well:

```bash
LAB_RUN_FULL_DEPLOY=1 docker compose run --rm ansible-control
```

The full run uses `access_control_deploy_method=synchronize` to copy the current
checkout from the control container to `/opt/backoffice-auth-server` on the
target, renders lab-only secrets into `.env.local`, runs `start.sh`, and runs
`bootstrap.sh`.

It also checks Caddy over HTTPS with internal certificates:

- `https://lab-auth.localhost/realms/access-control-mvp/.well-known/openid-configuration`
- `https://lab-iam.localhost/healthz`
- `https://lab-demo.localhost/healthz`

The full run configures the target Docker daemon with the `vfs` storage driver
and disables BuildKit for runtime commands. That keeps nested Docker practical
inside this disposable lab and is not the production VPS default.

## Clean Up

```bash
docker compose down -v
```

## Caveats

- The target needs privileged container support for nested Docker runtime tests.
- UFW and Docker-in-Docker behavior may differ from a real VPS kernel.
- Lab secrets are intentionally disposable and must not be reused outside this
  local Docker lab.
