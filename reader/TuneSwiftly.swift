import Foundation
import iTunesLibrary

let lib = try ITLibrary.init(apiVersion: "1.0")
if CommandLine.arguments.count == 1 {
    for item in lib.allMediaItems {
        if item.mediaKind == .kindSong {
            print(item.title)
            print(item.artist!.name!)
            print(item.location!)
        }
    }
} else {
    for playlist in lib.allPlaylists {
        if playlist.name == CommandLine.arguments[1] {
            for item in playlist.items {
                if item.mediaKind == .kindSong {
                    print(item.title)
                    print(item.artist!.name!)
                    print(item.location!)
                }
            }
            break
        }
    }
}
