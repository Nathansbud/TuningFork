on OutputTrack(track, thePath)
	do shell script "echo " & my ConvertToJSON(track) & " >> " & thePath
end OutputTrack

use framework "Foundation"

repeat until application "Spotify" is not running
	tell application "Spotify"
		set currentTrack to my TrackData(current track)
		set priorPosition to 0
		set hasLogged to false
		
		if player state is playing then
			repeat until currentTrack is not my TrackData(current track) or (player position as real) < priorPosition
				if not hasLogged and (((player position as real) > 30) or ((player position as real) > (theDuration of currentTrack) / 2)) then
					my OutputTrack(currentTrack, "/Users/zackamiton/Code/TuningFork/data/spotify_log.txt")
					set hasLogged to true
				end if
				delay 10
			end repeat
		end if
	end tell
end repeat


on TrackData(theTrack)
	tell application "Spotify"
		return {theId:id of theTrack as text, theName:name of theTrack as text, theArtist:(artist of theTrack) as text, theAlbum:album of theTrack as text, theDuration:(duration of theTrack as number) / 1000}
	end tell
end TrackData

-- God bless Obj-C users; modified from https://stackoverflow.com/questions/18062494/how-to-enumerate-the-keys-and-values-of-a-record-in-applescript
on ConvertToJSON(dict)
	set objCDictionary to current application's NSDictionary's dictionaryWithDictionary:dict
	set {jsonDictionary, anError} to current application's NSJSONSerialization's dataWithJSONObject:objCDictionary options:(current application's NSJSONWritingPrettyPrinted) |error|:(reference)
	
	return quoted form of ((current application's NSString's alloc()'s initWithData:jsonDictionary encoding:(current application's NSUTF8StringEncoding)) as text)
end ConvertToJSON