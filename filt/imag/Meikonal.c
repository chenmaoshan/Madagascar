/* Fast marching eikonal solver (3-D).

Takes: < velocity.rsf > time.rsf

*/
#include <math.h>

#include<rsf.h>

#include "fastmarch.h"

int main (int argc,char* argv[]) 
{
    int b1, b2, b3, n1, n2, n3, i, nshot, ndim, is,order,n123, *p;
    float br1, br2, br3, o1, o2, o3, d1, d2, d3, slow;
    float **s, *t, *v;
    char *sfile;
    bool isvel, plane[3];
    sf_file vel, time, shots;

    sf_init (argc, argv);
    vel = sf_input("in");
    time = sf_output("out");

    if (SF_FLOAT != sf_gettype(vel)) 
	sf_error("Need float input");
    if(!sf_histint(vel,"n1",&n1)) sf_error("No n1= in input");
    if(!sf_histint(vel,"n2",&n2)) sf_error("No n2= in input");
    if(!sf_histint(vel,"n3",&n3)) n3=1;

    if(!sf_histfloat(vel,"d1",&d1)) sf_error("No d1= in input");
    if(!sf_histfloat(vel,"d2",&d2)) sf_error("No d2= in input");
    if(!sf_histfloat(vel,"d3",&d3)) d3=d2;

    if(!sf_histfloat(vel,"o1",&o1)) o1=0.;
    if(!sf_histfloat(vel,"o2",&o2)) o2=0.;
    if(!sf_histfloat(vel,"o3",&o3)) o3=0.;

    if(!sf_getbool("vel",&isvel)) isvel=true;
    /* if y, the input is velocity; n, slowness */

    if(!sf_getint("order",&order)) order=2;
    /* [1,2] Accuracy order */

    if(!sf_getfloat("br1",&br1)) br1=d1;    
    if(!sf_getfloat("br2",&br2)) br2=d2; 
    if(!sf_getfloat("br3",&br3)) br3=d3;
    /* Constant-velocity box around the source (in physical dimensions) */
 
    if(!sf_getbool("plane1",&plane[2])) plane[2]=false;
    if(!sf_getbool("plane2",&plane[1])) plane[1]=false;
    if(!sf_getbool("plane3",&plane[0])) plane[0]=false;
    /* plane-wave source */

    if(!sf_getint("b1",&b1)) b1= plane[2]? n1: (int) (br1/d1+0.5); 
    if(!sf_getint("b2",&b2)) b2= plane[1]? n2: (int) (br2/d2+0.5); 
    if(!sf_getint("b3",&b3)) b3= plane[0]? n3: (int) (br3/d3+0.5); 
    /* Constant-velocity box around the source (in samples) */

    if( b1<1 ) b1=1;  
    if( b2<1 ) b2=1;  
    if( b3<1 ) b3=1;

    sfile = sf_getstring("shotfile");
    /* File with shot locations (n2=number of shots, n1=3) */

    if(NULL != sfile) {
	shots = sf_input("shotfile");

	if (SF_FLOAT != sf_gettype(shots)) 
	    sf_error("Need float shotfile");
	if(!sf_histint(shots,"n2",&nshot)) 
	    sf_error("No n2= in shotfile");
	if(!sf_histint(shots,"n1",&ndim) || ndim != 3) 
	    sf_error("Need n1=3 in shotfile");
  
	s = sf_floatalloc2 (ndim,nshot);
	sf_floatread(s[0],nshot*ndim,shots);
    
	sf_putint (time,"n4",nshot);
	free (sfile);
    } else {
	nshot = 1;
	ndim = 3;
    
	s = sf_floatalloc2 (ndim,nshot);     

	if(!sf_getfloat("zshot",&s[0][0])  ) s[0][0]=0.; 
	/* Shot location (used if no shotfile) */
	if(!sf_getfloat("yshot",&s[0][1])) s[0][1]=o2 + 0.5*(n2-1)*d2;
	if(!sf_getfloat("xshot",&s[0][2])) s[0][2]=o3 + 0.5*(n3-1)*d3;

	sf_warning("Shooting from zshot=%g yshot=%g xshot=%g",
		   s[0][0],s[0][1],s[0][2]);
    }

    n123 = n1*n2*n3;

    t  = sf_floatalloc (n123);
    v  = sf_floatalloc (n123);
    p  = sf_intalloc (n123);

    sf_floatread(v,n123,vel);
   /* transform velocity to slowness squared */
    if (isvel) {
	for(i = 0; i < n123; i++) {
	    slow = v[i];
	    v[i] = 1./(slow*slow);
	}
    } 
    
    fastmarch_init (n3,n2,n1);
  
    /* loop over shots */
    for( is = 0; is < nshot; is++) {
	fastmarch(t,v,p, plane,
		  n3,n2,n1,
		  o3,o2,o1,
		  d3,d2,d1,
		  s[is][2],s[is][1],s[is][0], 
		  b3,b2,b1,
		  order); 
	
	sf_floatwrite (t,n123,time);
    }
    
    sf_close();
    exit (0);
}

/* 	$Id: Meikonal.c,v 1.6 2004/06/18 01:06:45 fomels Exp $	 */

