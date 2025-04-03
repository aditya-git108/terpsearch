terpsearch: dist/ build/
	# Clean previous builds
	rm -rf dist build *.egg-info

	# Build package
	python3 -m build

	# Install locally for testing
	pip3 install .


install_requirements: requirements.txt
	pip3 install -r requirements.txt