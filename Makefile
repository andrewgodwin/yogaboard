.PHONY: build install clean help

# Flatpak configuration
APP_ID = org.aeracode.yogaboard
MANIFEST = $(APP_ID).json
BUILD_DIR = build-dir
REPO_DIR = flatpak-repo
BUNDLE = yogaboard.flatpak

# Use Flatpak-packaged flatpak-builder
FLATPAK_BUILDER = flatpak run org.flatpak.Builder

help:
	@echo "Yogaboard Flatpak Build System"
	@echo ""
	@echo "Available targets:"
	@echo "  make build    - Build Flatpak and create .flatpak bundle artifact"
	@echo "  make install  - Install the Flatpak bundle to user repo"
	@echo "  make clean    - Clean build artifacts"
	@echo "  make help     - Show this help message"

build:
	@echo "Building Flatpak..."
	$(FLATPAK_BUILDER) --user --repo=$(REPO_DIR) --force-clean --disable-rofiles-fuse $(BUILD_DIR) $(MANIFEST)
	@echo "Creating bundle artifact..."
	flatpak build-bundle $(REPO_DIR) $(BUNDLE) $(APP_ID)
	@echo ""
	@echo "Build complete! Artifact created: $(BUNDLE)"

install: $(BUNDLE)
	flatpak install --user -y $(BUNDLE)

clean:
	rm -rf $(BUILD_DIR) $(REPO_DIR) $(BUNDLE) yogaboard.egg-info

$(BUNDLE):
	@echo "Error: $(BUNDLE) not found. Run 'make build' first."
	@exit 1
