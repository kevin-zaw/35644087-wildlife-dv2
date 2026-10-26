# Downloading the all-wildlife data (about 10–20 minutes, mostly waiting)

The script `scripts/download_wildlife_data.py` asks the Atlas of Living Australia (ALA) for *counts* of wildlife records. It asks for counts by group, year, month, state, 1° square and data source. If the ALA is unreachable it switches to the GBIF API automatically.

It needs only Python 3.8 or newer. There is nothing to install, and you don't need an account or an API key.

## 1. One-time setup

1. **Install Python** (skip this if you already have it).
   - Windows: download it from <https://www.python.org/downloads/>. On the first installer screen, tick **"Add python.exe to PATH"**.
   - Mac: download it from the same page.
2. **Install VS Code** from <https://code.visualstudio.com/>.
3. **Add the Python extension.** Open VS Code, click the Extensions icon (four squares) on the left, search **Python** (by Microsoft) and click **Install**.
4. **Unzip** `wildlife-dv2.zip`.
5. **Open the folder.** In VS Code choose **File → Open Folder…**, select the `wildlife-dv2` folder (the one containing `index.html`) and click **Trust** if asked.

## 2. Run it

### Option A: buttons

1. Click the **Run and Debug** icon (a play triangle with a bug) on the left.
2. Pick **"1. Quick connection test"** from the dropdown at the top and press the green ▶. It should print `ALA OK` or `GBIF OK` and finish within about 30 seconds.
3. Pick **"2. Download all wildlife data"** and press ▶.

### Option B: terminal

Open **Terminal → New Terminal** and type:

```
python scripts/download_wildlife_data.py --test
python scripts/download_wildlife_data.py
```

- On Windows, if `python` is not found, use `py` instead.
- On a Mac, use `python3` instead.

### While it runs

The terminal prints `Step 1/9` … `Step 9/9`. Step 7 (the 1° grid) is the slowest.

When it finishes you'll see:

```
Done. Upload this file to Claude: …/results_for_claude.zip
```

## 3. Send the results back to Claude

**Upload the single file `results_for_claude.zip`** from the project folder (next to `index.html`) into the chat. Write a message such as:

> Here are the results from the download script.

The zip is small, usually well under 1 MB. It contains:

- the CSV tables;
- `manifest.json`, which records every query URL, the filters used and the time of the download (this goes into the page's metadata);
- `SUMMARY.txt` and `download_log.txt`.

If the chat won't accept the zip, upload the files from `data/ala/` instead. Upload the `.csv` files plus `manifest.json` and `SUMMARY.txt`; you can send them over two or three messages.

## Troubleshooting

| Message | Fix |
|---|---|
| `python is not recognized` | Reinstall Python with **Add to PATH** ticked, or use `py` (Windows) or `python3` (Mac). |
| `CERTIFICATE_VERIFY_FAILED` (Mac) | Open Finder → Applications → Python 3.x → double-click **Install Certificates.command**, then run again. As a last resort, add `--insecure`. |
| `HTTP 429` or `HTTP 503`, or many failures | The server is busy. Wait 10 minutes and run the same command again. Answers already received are cached, so it resumes where it stopped. |
| `ALA download stopped …` then GBIF lines | That's fine: the GBIF fallback is running. Upload the zip as normal. |
| University or work network blocks it | Try home internet or a phone hotspot. |
| You want to start completely fresh | Add `--fresh`. |

Run the script from the project folder: this is where VS Code's terminal opens by default after **File → Open Folder**.
