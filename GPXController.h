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
	
	IBOutlet NSTextField *gpsDevice;
	
	IBOutlet NSButton *processButton;
	IBOutlet WebView *webView;
	IBOutlet NSButton *writeXMPBox;
	IBOutlet NSButton *writeEXIFBox;
	IBOutlet NSProgressIndicator *progressIndication;
	// Windows
	IBOutlet NSWindow *mainWindow;
	IBOutlet NSWindow *progressWindow;
	IBOutlet NSWindow *gpsWindow;
}
-(IBAction)process:(id)sender;
-(IBAction)cancelTagging:(id)sender;
-(IBAction)selectGPX:(id)sender;
-(IBAction)selectImages:(id)sender;
// GPS Device Options
-(IBAction)gpsOptions:(id)sender;
-(IBAction)closeGPSOption:(id)sender;
-(IBAction)readFromGPS:(id)sender;
-(IBAction)eraseGPS:(id)sender;
-(IBAction)findGPSDevice:(id)sender;

-(void)handleExitingProcessing:(id)sender;

NSTask *gpxgeotag;
NSString *device;
@end
