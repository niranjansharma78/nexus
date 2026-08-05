# Nexus Python 3.14 setup

Copy these patch files into `D:\Nexus`, replacing existing files.

Then run:

```bat
scripts\clean_environment.bat
setup_only.bat
run.bat
```

Open `http://127.0.0.1:8010`.

After it works:

```bat
git add run.bat setup_only.bat requirements.txt pyproject.toml scripts docs
git commit -m "Fix Python 3.14 environment setup"
git push origin develop
```

If setup fails, share `D:\Nexus\nexus_diagnostic.txt` and the final visible error.
