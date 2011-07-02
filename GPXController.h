//
//  Controller.h
//  GPX Tagger
//
//  Created by Ian Molloy on 6/28/11.
//  Copyright 2011 PerpetualMotionFuel. All rights reserved.
//

#import <Cocoa/Cocoa.h>
#import <WebKit/WebKit.h>

@interface GPXController : NSObject {
	IBOutlet NSTextField *gpxField;
	IBOutlet NSTextField *imagesField;
	IBOutlet NSTextField *hourField;
	IBOutlet NSTextField *minuteField;
	IBOutlet NSTextField *secondField;
	IBOutlet NSButton *processButton;
	IBOutlet WebView *webView;
	IBOutlet NSButton *writeXMPBox;
	IBOutlet NSButton *writeEXIFBox;
	IBOutlet NSProgressIndicator *progressIndication;
}
-(IBAction)process:(id)sender;
-(IBAction)selectGPX:(id)sender;
-(IBAction)selectImages:(id)sender;
NSTask *gpxgeotag;
@end
