.PHONY: usage
usage:
	@ # Scrape together usage from # USAGE comments
	@grep "^# USAGE" Makefile | cut -d" " -f3-

.PHONY: install
# No usage statement here as this will be called manually by run
# in order to keep usage statements for standard commands together
install:  .@install_poetry_dev
	@echo "All dependencies installed"

.@install_poetry_dev: pyproject.toml poetry.lock
	poetry install
	@touch $@

poetry.lock:
	# touch but don't create the file
	@touch -c $@
