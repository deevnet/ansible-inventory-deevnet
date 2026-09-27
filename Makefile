VAULT_FILES := $(shell find . -name 'vault.yml' -not -path './.git/*')

.PHONY: help vault unvault install-hooks vault-examples empty-vault

default: help

help:
	@echo "Deevnet Inventory"
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  vault           Encrypt all unencrypted vault.yml files"
	@echo "  unvault         Decrypt all encrypted vault.yml files"
	@echo "  install-hooks   Set git hooks path to hooks/"
	@echo "  vault-examples  Regenerate vault.example.yml files (vaults must be decrypted)"
	@echo "  empty-vault     Create empty vault.yml files from the examples (SITE=mobile)"

vault:
	@TO_ENCRYPT=""; \
	for f in $(VAULT_FILES); do \
		if ! head -1 "$$f" | grep -q '^\$$ANSIBLE_VAULT'; then \
			TO_ENCRYPT="$$TO_ENCRYPT $$f"; \
		else \
			echo "Already encrypted: $$f"; \
		fi \
	done; \
	if [ -n "$$TO_ENCRYPT" ]; then \
		echo "Encrypting:$$TO_ENCRYPT"; \
		ansible-vault encrypt $$TO_ENCRYPT; \
	else \
		echo "All vault files already encrypted."; \
	fi

unvault:
	@TO_DECRYPT=""; \
	for f in $(VAULT_FILES); do \
		if head -1 "$$f" | grep -q '^\$$ANSIBLE_VAULT'; then \
			TO_DECRYPT="$$TO_DECRYPT $$f"; \
		else \
			echo "Already decrypted: $$f"; \
		fi \
	done; \
	if [ -n "$$TO_DECRYPT" ]; then \
		echo "Decrypting:$$TO_DECRYPT"; \
		ansible-vault decrypt $$TO_DECRYPT; \
	else \
		echo "All vault files already decrypted."; \
	fi

install-hooks:
	git config core.hooksPath hooks
	@echo "Git hooks path set to hooks/."

vault-examples:
	@python3 scripts/vault-examples.py

empty-vault:
	@scripts/make-empty-vault.sh $(or $(SITE),mobile)
