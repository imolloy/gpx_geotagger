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
											 selector:@selector(finishedDownload:) 
												 name:NSTaskDidTerminateNotification 
											   object:nil];
	gpxgeotag = nil; // This is a good time to initialize the pointer
	return self;
}

- (void)finishedDownload:(NSNotification *)aNotification {
	[processButton setTitle:@"Process"];
	[processButton setEnabled:YES];
	[gpxgeotag release]; // Don't forget to clean up memory
	gpxgeotag = nil; // Just in case...
	// And render the results
	//NSString *absolutePath = [shortPath stringByExpandingTildeInPath];
	// initFileURLWithPath
	NSString *indexPath = @"~/Library/Application%20Support/GPX%20Tagger/index.html";
	[[webView mainFrame] loadRequest:[NSURLRequest requestWithURL:[NSURL URLWithString:[indexPath stringByExpandingTildeInPath]]]];
}

- (IBAction)process:(id)sender {
	NSLog(@"The User pressed process");
	[processButton setEnabled:NO];
	gpxgeotag = [[NSTask alloc] init];
	[gpxgeotag setLaunchPath:@"/usr/bin/python"];
	[gpxgeotag setArguments:[NSArray arrayWithObjects:@"../../geotag.py", 
							 @"--hours", [hourField stringValue], 
							 @"--minutes", [minuteField stringValue], 
							 @"--seconds", [secondField stringValue], 
							 @"--gpx", [gpxField stringValue],
							 @"-i", [imagesField stringValue],
							 @"--maps", @"~/Library/Application Support/GPX Tagger",
							 nil]];
	[gpxgeotag launch];
}
@end
