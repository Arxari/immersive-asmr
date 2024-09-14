### Experience ASMR !!!NOW WITH ZAPPIES!!!
An openshock/python "framework" which maps shocks to parts of an .mp3 file similarly to how subtitles work, but instead of displaying text you get zapped!

### Usage

You have to have a .env file that's formatted like this:
```
SHOCK_API_KEY=enteryourapikeyhere
SHOCK_ID=enteryourshockeridhere
```

You run the script like this:
```
python player.py /path/to/audio/file.mp3
```

For now if you want to make using this script easier, on linux you can add this line to your .bashrc/zshrc file:
```
alias play='python3 /path/to/your/player.py'
```
Then you can just use ```play /path/to/audio/file.mp3``` to play the file.

<details open>
<summary><h3>✨ Planned Features ✨</h3></summary>

- Ability to easily share and import .txt files for audio files
- Easy setup for the API and Shock ID
- Web UI (and a publicly hosted instance)
</details open>
