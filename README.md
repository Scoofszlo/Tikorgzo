# Tikorgzo

**Tikorgzo** is a TikTok video downloader written in Python that downloads videos in the highest available quality and saves them to your Downloads folder, organized by username. The project utilizes Playwright to get download links from <b>[TikWM](https://www.tikwm.com/)</b> API. Currently, the project supports Windows only (for now).

Some of the key features include:

- Download TikTok video from command-line just by supplying the ID or video link.
- Supports multiple links to be downloaded.
- Supports link extraction from a text file.
- Extracts downloads link asynchronously for faster link extraction.

## Quickstart

Hhere is a short, quick installation and usage guide for this program.

### Requirements
- Windows
- Python `v3.10` or greater
- uv

### Steps
1. Install Python 3.10.0 or above. For Windows users, ensure `Add Python x.x to PATH` is checked.
2. Open your command-line.
3. Install uv through `pip` command or via [Standalone installer](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer).

    ```console
    pip install uv
    ```

4. Install the latest development release of Tikorgzo into your system.

    ```console
    uv tool install git+https://github.com/Scoofszlo/Tikorgzo
    ```

5. Install the Playwright browser. This is needed to allow download link extraction from the API.

    ```console
    uvx playwright install
    ```

6. To download a single TikTok video, simply run this:
  
    ```console
    tikorgzo -l 7123456789109876543
    ```

7. Wait for the program to do it's thing. The downloaded video should appear in your Downloads folder.

## Usage

### Downloading a video

To download a TikTok video, simply add put the video ID, or the video link:

```console
tikorgzo -l 7123456789109876543
```

### Downloading multiple videos

The program supports multiple video links to download. Simply separate those links by spaces:

```console
tikorgzo -l 7123456789109876543 7023456789109876544 "https://www.tiktok.com/@username/video/7123456789109876540"
```
### Downloading multiple links from a `.txt` file

Alternatively, you can also use a `.txt` file containing multiple video links and use it to download those. Ensure that each link are separated by newline.

To do this, just simply put the path to the `.txt` file.

```console
tikorgzo -f "C:\path\to\txt.file"
```

## Reminders
- Source/high-quality videos may not always be available, depending on the source. If not available, the downloaded videos are usually 1080p or 720p.
- The program may be a bit slow during download link extraction (Stage 2), as it runs a browser in the background to extract the actual download link.
- For this reason, the program is much more aligned to those who want to download multiple videos at once. However, you can still use it to download any number of videos you want.

## Documentation

Currently, there is no external site for project documentation. All documentation will be maintained within this README.md for now. If the README.md becomes too lengthy, a dedicated documentation site will be created and the relevant content will be moved there.

## License

Tikorgzo is an open-source program licensed under the [MIT](LICENSE) license.

If you can, please contribute to this project by suggesting a feature, reporting issues, or make code contributions!

## Legal Disclaimer

The use of this software to download content without the permission may violate copyright laws or TikTok's terms of service. The author of this project is not responsible for any misuse or legal consequences arising from the use of this software. Use it at your own risk and ensure compliance with applicable laws and regulations.

This project is not affiliated, endorsed, or sponsored by TikTok or its affiliates. Use this software at your own risk.

## Acknowledgements

Special thanks to <b>[TikWM](https://www.tikwm.com/)</b> for providing free API service, which serves as a way for this program to extract high quality TikTok videos.

## Contact

For questions or concerns, feel free to contact me via the following!:
- [Gmail](mailto:scoofszlo@gmail.com) - scoofszlo@gmail.com
- Discord - @scoofszlo
- [Reddit](https://www.reddit.com/user/Scoofszlo/) - u/Scoofszlo
- [Twitter](https://twitter.com/Scoofszlo) - @Scoofszlo
