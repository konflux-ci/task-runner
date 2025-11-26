.PHONY: venv
venv: .venv

.PHONY: .venv
.venv:
	uv sync

.PHONY: rpms.lock.yaml
rpms.lock.yaml:
	# rpm-lockfile-prototype depends on dnf bindings (the python3-dnf package on fedora)
	#   => need --system-site-packages
	uv venv --allow-existing --system-site-packages .rpm-lock-venv
	UV_PROJECT_ENVIRONMENT=.rpm-lock-venv uv run --group rpm-lock \
		rpm-lockfile-prototype deps/rpm/rpms.in.yaml --outfile deps/rpm/rpms.lock.yaml
