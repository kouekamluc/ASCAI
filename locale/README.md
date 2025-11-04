# Translation Files

This directory contains translation files for the ASCAI platform.

## Languages Supported
- English (en)
- French (fr)
- Italian (it)

## Generating Translation Files

To create or update translation files, run:

```bash
python manage.py makemessages -l en
python manage.py makemessages -l fr
python manage.py makemessages -l it
```

This requires GNU gettext tools to be installed.

On Windows:
- Download from: https://mlocati.github.io/articles/gettext-iconv-windows.html
- Or use WSL (Windows Subsystem for Linux)

On macOS:
```bash
brew install gettext
```

On Linux:
```bash
sudo apt-get install gettext  # Ubuntu/Debian
sudo yum install gettext      # CentOS/RHEL
```

## Compiling Translations

After editing translation files, compile them:

```bash
python manage.py compilemessages
```

## Translation Files Structure

```
locale/
├── en/
│   └── LC_MESSAGES/
│       └── django.po (English translations)
├── fr/
│   └── LC_MESSAGES/
│       └── django.po (French translations)
└── it/
    └── LC_MESSAGES/
        └── django.po (Italian translations)
```






