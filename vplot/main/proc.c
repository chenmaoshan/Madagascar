/*
 * Copyright 1987 the Board of Trustees of the Leland Stanford Junior
 * University. Official permission to use this software is included in
 * the documentation. It authorizes you to use this file for any
 * non-commercial purpose, provided that this copyright notice is not
 * removed and that any modifications made to this file are commented
 * and dated in the style of my example below.
 */

/*
 *
 *  source file:   ./filters/proc_vplot.c
 *
 * Joe Dellinger (SEP), Feb 19 1988
 *	Inserted this sample edit history entry.
 *	Please log any further modifications made to this file:
 *
 * Joe Dellinger Feb 22 1988
 *	Created INT_PAUSE to be separate from INT_GET_STRING.
 * Joe Dellinger Feb 27 1988
 *	Interact option turns of endpausing.
 * W. Bauske IBM 03-26-91 
 *	Apply SysV fixes for RS/6000
 * Stew Levin MOBIL 2-27-95
 *	Solaris mods
 & Bob Clapp
 *  Changed signals from BSD to POSIX1 for LINUX
 */
#include <sitedef.h>

#include	<stdio.h>
#include	<math.h>
#define		GETPAR	getpar


#if defined(HAVE_TERMIO_H)
#include	<termio.h>
#else /* USG */
#ifdef LINUX
#include	<bsd/sgtty.h>
#else
#include	<sys/ioctl.h>
#include	<sgtty.h>
#endif
#endif /* USG */
#include	<sys/types.h>
#include	<sys/stat.h>
#include	<ctype.h>
#include	<string.h>

#include	<vplot.h>

#include	"./include/params.h"	/* for machine dependencies */
#include	"./include/enum.h"
#include	"./include/err.h"
#include	"./include/attrcom.h"
#include	"./include/intcom.h"
#include	"./include/mesgcom.h"
#include	"./include/erasecom.h"
#include	"./include/closestat.h"
#include	"./include/pat.h"
#include	"./include/vertex.h"
#include	"./include/round.h"
#include	"./include/extern.h"

#if defined (HAVE_TERMIO_H)
extern struct termio tty_clean_state;
#else /* USG */
extern struct sgttyb tty_clean_state;
extern int      tty_clean_local_mode;
#endif /* USG */
extern int      need_end_erase;
extern int      buffer_input;
extern int      ever_called;
extern int      out_isatty;
extern int      nplots;
extern int      endpause;
extern int      allowecho;
extern int      epause;
extern char     interact[];
extern int      pltoutfd;
extern int      (*message) ();
extern FILE    *pltin;
extern FILE    *controltty;
extern FILE    *pltinarray[];
extern char     pltinname[][MAXFLEN + 1];
extern char     pltname[];
extern int      infileno;
extern int      (*genreader) ();

FILE           *fopen ();

/*
 * This routine is responsible for processing the input files,
 * and performing the necessary pausing, etc, that may be needed
 * at the end before exiting.
 */

proc_vplot ()
{
int             ii;
char            string[MAXFLEN + 1];

/*
 * Finally, shove all the plot files off to be done!
 */

/*	fprintf(stderr,"i am in process plot \n");*/
    if (!buffer_input)
    {
	for (ii = 0; ii < infileno; ii++)
	{
/*	fprintf(stderr,"2 am in process plot \n");*/
	    setbuf (pltinarray[ii], (char *) NULL);
/*	fprintf(stderr,"3 am in process plot \n");*/
	}
    }
/*	fprintf(stderr,"3b am in process plot \n");*/

    (*genreader) (infileno, pltinarray, pltinname);

/*	fprintf(stderr,"4 am in process plot \n");*/
/*
 * Normally, *genreader will be gen_do_dovplot, found in genlib
 */

    if (ever_called)
    {
	dev.close (CLOSE_FLUSH);
	if (epause > 0)
	{
	    sleep ((unsigned) epause);
	}
	if (need_end_erase)
	{
	    dev.erase (ERASE_END);
	}
	/*
	 * Inquire point back from device. Skip endpause stuff if we do
	 * interact, Since that's a pause in itself. 
	 */
	if (interact[0] != '\0')
	{
	    getapoint ();
	}
	else
	{

/*
 * Pause at the end if the user specifically asks us to on the command line,
 * even if we don't think we should because we think it's a file.
 */
	    if (epause <= 0 &&
		(out_isatty || getpar ("endpause", "s", string))
		&& endpause)
	    {
		dev.close (CLOSE_PAUSE);
		dev.interact (INT_F_PAUSE, controltty, string);
	    }
	}
	message (MESG_ON);
	dev.close (CLOSE_NORMAL);
	dev.close (CLOSE_DONE);
	nplots++;
    }
    else
    {
	dev.close (CLOSE_NOTHING);
	ERR (COMMENT, name, "No input?");
	dev.close (CLOSE_DONE);
    }

    /*
     * Done, let them see what they are doing again 
     */
    if (!allowecho)
    {
#if defined(HAVE_TERMIO_H)
	if (ioctl (pltoutfd, TCSETAW, &tty_clean_state) == -1)
	{
		ERR (FATAL, name, "Bad ioctl call!");
	}
#else /* USG */
	ioctl (pltoutfd, TIOCLSET, (char *) (&tty_clean_local_mode));
	ioctl (pltoutfd, TIOCSETN, (char *) (&tty_clean_state));
#endif /* USG */
    }
}
