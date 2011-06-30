//
//  Controller.m
//  GPX Tagger
//
//  Created by Ian Molloy on 6/28/11.
//  Copyright 2011 IBM T.J. Watson. All rights reserved.
//

#import "GPXController.h"

@implementation GPXController
- (id)init {
    self = [super init];
    [[NSNotificationCenter defaultCenter] addObserver:self 
											 selector:@selector(finishedTagging:) 
												 name:NSTaskDidTerminateNotification 
											   object:nil];
	gpxgeotag = nil; // This is a good time to initialize the pointer
	return self;
}

- (void)finishedTagging:(NSNotification *)aNotification {
	[processButton setTitle:@"Process"];
	[processButton setEnabled:YES];
	[gpxgeotag release]; // Don't forget to clean up memory
	gpxgeotag = nil; // Just in case...
	// And render the results
	NSString *indexPath = @"~/Library/Application%20Support/GPX%20Tagger/index.html";
	[[webView mainFrame] loadRequest:[NSURLRequest requestWithURL:[NSURL URLWithString:[indexPath stringByExpandingTildeInPath]]]];
	[progressIndication stopAnimation:self];
	[progressIndication release];
}

- (IBAction)process:(id)sender {
	NSLog(@"The User pressed process");
	[processButton setEnabled:NO];
	gpxgeotag = [[NSTask alloc] init];
	[gpxgeotag setLaunchPath:@"/usr/bin/python"];
	NSString *path = [[NSBundle mainBundle] pathForResource:@"geotag" ofType:@"py"];
	NSMutableArray *args = [NSMutableArray arrayWithObjects:path, 
							 @"--hours", [hourField stringValue], 
							 @"--minutes", [minuteField stringValue], 
							 @"--seconds", [secondField stringValue], 
							 @"--gpx", [gpxField stringValue],
							 @"-i", [imagesField stringValue],
							 @"--maps", @"~/Library/Application Support/GPX Tagger", nil];
	if (NSOnState == [writeXMPBox state]) {
		[args addObject:@"-x"];
	}
	if (NSOnState == [writeEXIFBox state]) {
		[args addObject:@"-e"];
	}
	[gpxgeotag setArguments:args];
	progressIndication = [[NSProgressIndicator alloc] init];
	[progressIndication setUsesThreadedAnimation:YES];
	[progressIndication startAnimation:self];
	[gpxgeotag launch];
}

-(IBAction)selectGPX:(id)sender {
	NSOpenPanel *op = [NSOpenPanel openPanel];
	[op setCanChooseFiles:YES];
	[op setCanChooseDirectories:NO];
	if ([op runModal] == NSOKButton) {
		NSString *filename = [op filename];
		[gpxField setStringValue:filename];
    }
}

-(IBAction)selectImages:(id)sender {
	NSOpenPanel *op = [NSOpenPanel openPanel];
	[op setCanChooseFiles:NO];
	[op setCanChooseDirectories:YES];
	if ([op runModal] == NSOKButton) {
		NSString *filename = [op filename];
		[imagesField setStringValue:filename];
    }
}
@end
