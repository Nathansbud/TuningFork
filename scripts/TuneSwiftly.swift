import Foundation
import iTunesLibrary

let lib = try ITLibrary.init(apiVersion: "1.0")
for item in lib.allMediaItems {
    if item.mediaKind == .kindSong {
        if item.comments != nil && item.comments!.contains("Vocal") && !item.comments!.contains("Imbecile") {
            print(item.title)
            print(item.artist!.name!)
            print(item.location!)
        }
    }
}

