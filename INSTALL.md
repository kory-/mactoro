# Mactoro Installation Guide

## For Developers (Testing locally)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mactoro.git
cd mactoro
```

2. Install in development mode:
```bash
pip install -e .
```

3. Test the installation:
```bash
mactoro --version
mactoro window list
```

## Publishing to PyPI

1. Build the package:
```bash
python setup.py sdist bdist_wheel
```

2. Upload to PyPI:
```bash
pip install twine
twine upload dist/*
```

## Creating Homebrew Formula

1. Create a GitHub release with tag `v0.1.0`

2. Get the SHA256 of the tarball:
```bash
curl -L https://github.com/yourusername/mactoro/archive/v0.1.0.tar.gz | shasum -a 256
```

3. Update `homebrew-formula.rb` with the correct SHA256 values

4. Create a Homebrew tap repository:
```bash
# Create repo: homebrew-mactoro on GitHub
git clone https://github.com/yourusername/homebrew-mactoro.git
cp homebrew-formula.rb homebrew-mactoro/Formula/mactoro.rb
cd homebrew-mactoro
git add .
git commit -m "Add mactoro formula"
git push
```

5. Users can then install via:
```bash
brew tap yourusername/mactoro
brew install mactoro
```

## Development Structure

```
mactoro/
├── mactoro/              # Package directory
│   ├── __init__.py
│   ├── cli.py           # Main CLI entry point
│   ├── window_controller.py
│   ├── action_recorder.py
│   └── coordinate_helper.py
├── example/             # Example configurations
├── setup.py            # Package configuration
├── requirements.txt    # Dependencies
├── README.md          # Documentation
└── LICENSE            # MIT License
```