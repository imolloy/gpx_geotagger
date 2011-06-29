//
//  GPX_TaggerAppDelegate.h
//  GPX Tagger
//
//  Created by Ian Molloy on 6/27/11.
//  Copyright 2011 IBM T.J. Watson. All rights reserved.
//

#import <Cocoa/Cocoa.h>

@interface GPX_TaggerAppDelegate : NSObject <NSApplicationDelegate> {
    NSWindow *window;
}

@property (assign) IBOutlet NSWindow *window;

@end
