//
//  Controller.m
//  GPX Tagger
//
//  Created by Ian Molloy on 6/28/11.
//  Copyright 2011 PerpetualMotionFuel. All rights reserved.
//

#import "GPXController.h"
#import <util.h>
#include <sys/ioctl.h>
#include <unistd.h>

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
	NSLog(@"Termination Notification %@", [aNotification name]);
	NSLog(@"Termination Object %@", [aNotification object]);
	NSLog(@"Command: %@ Finished", [[aNotification object] launchPath]);
	if ([[aNotification object] launchPath] != @"/usr/bin/python")
		return [self handleExitingProcessing:aNotification];
	NSLog(@"Python geotag.py finished.");
	[processButton setTitle:@"Process"];
	[processButton setEnabled:YES];
	int pythonStatus = [gpxgeotag terminationStatus];
	NSLog(@"Python script termination code: %d", pythonStatus);
	[gpxgeotag release]; // Don't forget to clean up memory
	gpxgeotag = nil; // Just in case...
	// And render the results
	NSString *indexPath = @"~/Library/Application%20Support/GPX%20Tagger/index.html";
	[[webView mainFrame] loadRequest:[NSURLRequest requestWithURL:[NSURL URLWithString:[indexPath stringByExpandingTildeInPath]]]];
	[progressIndication stopAnimation:self];
	[progressWindow orderOut:nil];
    [NSApp endSheet:progressWindow];
	[progressIndication setDoubleValue:0.0];
	if (pythonStatus != 0) {
		NSAlert *theAlert = [[[NSAlert alloc] init] autorelease];
		//[theAlert addButtonWithTitle:@"Error processing GPX file"];
		[theAlert setMessageText:@"Error processing GPX file."];
		[theAlert setInformativeText:@"There was an error running the Python scripts to geotag images. Verify the GPX file exists, the image directory exists, and the the files are readable. Please verify settings, check the Console, or email your son."];
		[theAlert addButtonWithTitle:@"Ok"];
		[theAlert setAlertStyle:NSWarningAlertStyle];
		[theAlert beginSheetModalForWindow:mainWindow
							 modalDelegate:nil
							didEndSelector:nil 
							   contextInfo: nil];
	}
}

-(void)handleExitingProcessing:(id)sender {
	NSLog(@"Assuming gpsbabel exited");
}

- (IBAction)process:(id)sender {
	[processButton setEnabled:NO];
	gpxgeotag = [[NSTask alloc] init];
	NSString *exifPath = [[NSBundle mainBundle] pathForResource:@"exiftool" ofType:@""];
	NSLog(@"Found exiftool at %@", exifPath);
	[gpxgeotag setLaunchPath:@"/usr/bin/python"];
	NSString *path = [[NSBundle mainBundle] pathForResource:@"geotag" ofType:@"pyc"];
	NSMutableArray *args = [NSMutableArray arrayWithObjects:path, 
							@"--hours", [hourField stringValue], 
							@"--minutes", [minuteField stringValue], 
							@"--seconds", [secondField stringValue], 
							@"--gpx", [gpxField stringValue],
							@"-i", [imagesField stringValue],
							@"--maps", @"~/Library/Application Support/GPX Tagger", 
							@"--exiftool", exifPath,
							nil];
	if (NSOnState == [writeXMPBox state]) {
		[args addObject:@"-x"];
	}
	if (NSOnState == [writeEXIFBox state]) {
		[args addObject:@"-e"];
	}
	[gpxgeotag setArguments:args];
	NSLog(@"Starting geotagging process with: %@", args);
	// The following solution to read output not from an NSPipe taken from http://amath.colorado.edu/pub/mac/programs/
	int masterfd, slavefd;
	char devname[64];
	if (openpty(&masterfd, &slavefd, devname, NULL, NULL) == -1)
	{
		[NSException raise:@"OpenPtyErrorException"
					format:@"%s", strerror(errno)];
	}
	NSFileHandle* slaveFH = [[NSFileHandle alloc] initWithFileDescriptor:slavefd];
	NSFileHandle* masterFH = [[NSFileHandle alloc] initWithFileDescriptor:masterfd
														   closeOnDealloc:YES];
	[gpxgeotag setStandardOutput:slaveFH];
	[[NSNotificationCenter defaultCenter] addObserver:self
											 selector:@selector(getData:)
												 name:NSFileHandleReadCompletionNotification
											   object:masterFH];
	[progressIndication startAnimation:self];
	[progressIndication setUsesThreadedAnimation:YES];
	[NSApp beginSheet:progressWindow
	   modalForWindow:mainWindow
        modalDelegate:self
	   didEndSelector:NULL
		  contextInfo:nil];
	[masterFH readInBackgroundAndNotify];
	[gpxgeotag launch];
}

-(IBAction)cancelTagging:(id)sender {
	[gpxgeotag terminate];
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

- (void)getData:(NSNotification *)aNotification
{
	//NSLog(@"Received Data...\n");
	NSData * data = [[aNotification userInfo] objectForKey:NSFileHandleNotificationDataItem];
	
    if ([data length] == 0)
        return; // end of file
	
    NSString * str = [[NSString alloc] initWithData:data encoding:NSUTF8StringEncoding];
	NSScanner *scanner = [NSScanner scannerWithString:str];
	double val = 0;
	while ([scanner scanDouble:&val]) {
		[progressIndication setDoubleValue:val];
	}
	[[aNotification object] readInBackgroundAndNotify];
}

-(void)gpsOptions:(id)sender {
	NSLog(@"Opening GPS Device options to use GPSBabel...\n");
	NSError *anError = [[NSError alloc] init];
	NSArray *dirContents = [[NSFileManager defaultManager] 
							contentsOfDirectoryAtPath:@"/dev" error:&anError];
	// NSLog(@"Contents of /dev: %@", dirContents);
	// NSString *foo = [[NSString alloc] initWithCString: "cu.usbmodemfa140"];
	// NSLog(@"Test prefix %d", [foo hasPrefix:@"cu.usbmodemfa"]);
	// NSLog(@"Test prefix %d", [foo hasPrefix:@"cu.usbmodedga"]);
	
	NSEnumerator * enumerator = [dirContents objectEnumerator];
	id element;
	device = [[NSString alloc] initWithCString:"None Found"];
	while(element = [enumerator nextObject]) {
		if ([element hasPrefix:@"cu.usbmodemfa"]) {
			NSLog(@"Possible GPS Device: %@", element);
			[device release];
			//device = [[NSString alloc] initWithString:element];
			device = [[NSString alloc] initWithFormat:@"/dev/%@", element];
		}
    }
	[gpsDevice setStringValue:device];
	[NSApp beginSheet:gpsWindow
	   modalForWindow:mainWindow
        modalDelegate:self
	   didEndSelector:NULL
		  contextInfo:nil];
}

-(void)closeGPSOption:(id)sender {
	[gpsWindow orderOut:self];
    [NSApp endSheet:gpsWindow];
}

- (void)readFromGPS:(id)sender {
	NSString *bablePath = [[NSBundle mainBundle] pathForResource:@"gpsbabel" ofType:@""];
	NSTask *babelTask = [[NSTask alloc] init];
	// -t  -i mtk -f /dev/cu.usbmodemfd130 -o gpx -F ~/Desktop/foobar.gpx
	[babelTask setLaunchPath:bablePath];
	NSMutableArray *args = [NSMutableArray arrayWithObjects: 
	 @"-t", 
	 @"-i", @"mtk", 
	 @"-f", device, 
	 @"-o", @"gpx",
	 @"-F", [@"~/Desktop/foobars.gpx" stringByExpandingTildeInPath],
	 nil];
	[babelTask setArguments:args];
	[babelTask launch];
	[babelTask waitUntilExit];
	int status = [babelTask terminationStatus];
	if (status == 0) {
		[gpxField setStringValue:[@"~/Desktop/foobars.gpx" stringByExpandingTildeInPath]];
	}
	[babelTask release];
	[gpsWindow orderOut:self];
    [NSApp endSheet:gpsWindow];
	NSLog(@"Reading from GPS Device Return Code:%d", status);
}

-(void)eraseGPS:(id)sender {
	NSLog(@"Erasing GPS file\n");
	// gpsbabel -t -w -i mtk,erase -f /dev/cu.usbmodemfd130
	// Should probably first open an "are you sure?" modal...
}

@end
