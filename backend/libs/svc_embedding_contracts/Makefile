SPEC_UPSTREAM := openapi.upstream.json
SPEC_PATCHED := openapi.patched.json
PATCH_FILES := $(wildcard patches/*.json)
MODELS_DIR := src/svc_embedding_contracts/models
PATCH_SCRIPT := tools/apply_json_patches.py


.PHONY: gen patch clean
.DEFAULT_GOAL := gen

patch:
ifeq ($(wildcard $(PATCH_SCRIPT)),)
	@echo "No patch script found, skipping patching..."
	@cp $(SPEC_UPSTREAM) $(SPEC_PATCHED)
else
ifneq ($(strip $(PATCH_FILES)),)
	@echo "Applying patches..."
	python tools/apply_json_patches.py $< $(PATCH_FILES)
else
	@echo "No patches found, copying upstream spec..."
	cp $(SPEC_UPSTREAM) $(SPEC_PATCHED)
endif
endif
	@echo "Spec patched: $@"

gen: patch
	@mkdir -p $(MODELS_DIR)
	datamodel-codegen \
		--input $(SPEC_PATCHED) --input-file-type openapi \
		--output $(MODELS_DIR)/__init__.py \
		--target-python-version 3.13 \
		--output-model-type pydantic_v2.BaseModel \
		--use-double-quotes --use-standard-collections \
		--use-field-description \
		--parent-scoped-naming \
		--disable-future-imports \
		--collapse-root-models \
		--openapi-scopes paths \
		--use-default-kwarg \
		--use-title-as-name \
		--strict-nullable \
		--snake-case-field
	@echo "Models generated : $(MODELS_DIR)"

clean:
	rm -rf build $(MODELS_DIR) $(SPEC_PATCHED)