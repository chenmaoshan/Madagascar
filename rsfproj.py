import os, stat, sys, types, commands, re, string, urllib
import rsfdoc
import rsfprog
import rsfconf

# The following adds all SCons SConscript API to the globals of this module.
import SCons.Script.SConscript
globals().update(SCons.Script.SConscript.BuildDefaultGlobals())

##############################################################################
# BEGIN CONFIGURATION VARIABLES
##############################################################################

#prefix for rsf commands
sfprefix = 'sf'
#prefix for vpl commands
plprefix = 'vp'
#suffix for rsf files
sfsuffix = '.rsf'
# suffix for vplot files
vpsuffix = '.vpl'
# suffix for eps files
pssuffix = '.eps'
# path bor binary files
datapath = os.environ.get('DATAPATH')
if not datapath:
    try:
        file = open('.datapath','r')
    except:
        try:
            file = open(os.path.join(os.environ.get('HOME'),'.datapath'),'r')
        except:
            file = None
    if file:
        for line in file.readlines():
            check = re.match("(?:%s\s+)?datapath=(\S+)" % os.uname()[1],line)
            if check:
                datapath = check.group(1)
        file.close()
    if not datapath:
        datapath = os.path.join(os.environ.get('HOME'),'')
rdatapath = os.environ.get('RDATAPATH',
                           'ftp://begpc132.beg.utexas.edu/data/')

# directory tree for executable files
top = os.environ.get('RSFROOT')
bindir = os.path.join(top,'bin')
libdir = os.path.join(top,'lib')
incdir = os.path.join(top,'include')

resdir = './Fig'
record = 0

def set_resdir(dir):
     global resdir
     resdir = dir

def Book():
    global record
    set_resdir('../Fig')
    record = 1

def Standalone():
    global record
    set_resdir('./Fig')
    record = 0

Book()

latex = None
bibtex = None
rerun = None

# temporary (I hope)
sep = os.path.join(os.environ.get('SEP'),'bin/')

##############################################################################
# END CONFIGURATION VARIABLES
##############################################################################

def collect_exe(dir):
    "Make a list of executable files in a directory"
    def isexe(file):
        "Check if a file is executable" # Posix only?
        return (os.stat(file)[stat.ST_MODE] &
                (stat.S_IXUSR|stat.S_IXGRP|stat.S_IXOTH))
    exe = []
    for file in os.listdir(dir):
        file = os.path.join(dir,file)
        if os.path.isfile(file) and isexe(file):
            exe.append(file)
    return exe

#############################################################################
# CUSTOM BUILDERS
#############################################################################

#def clean(target=None,source=None,env=None):
#    for junk in env['junk']:
#        if (os.path.isfile (junk)):
#            try:
#                os.unlink(junk)
#            except:
#                pass
#    return 0

def silent(target=None,source=None,env=None):
    return None

ppi = 72 # points per inch resolution
def pstexpen(target=None,source=None,env=None):
    "Convert vplot to EPS"
    vplot = str(source[0])
    eps = str(target[0])
    space = os.environ.get('PSBORDER')
    if not space:
        space=0.
    else:
        space=float(space)
    opts = os.environ.get('PSTEXPENOPTS')
    if not opts:
        opts = ''
    pstexpenopts = env.get('opts')
    if not pstexpenopts:
        pstexpenopts = 'color=n fat=1 fatmult=1.5 invras=y'
    opts = string.join([opts,pstexpenopts],' ')
    print opts
    head = string.split(
        commands.getoutput(sep +
                           "vppen big=n stat=l %s < %s | %s -1" %
                           (opts,vplot,WhereIs('head'))))
    bb = []
    for x in (7, 12, 9, 14):
        bb.append(int((float(head[x])-space)*ppi))
    try:
        file = open(eps,"w")
        file.write("%\!PS-Adobe-2.0 EPSF-2.0\n")
        file.write("%%%%BoundingBox: %d %d %d %d\n" % tuple(bb))
        file.write(commands.getoutput(sep + "pspen size=a tex=y %s < %s" %
                                      (opts,vplot)))
        file.write("\n")
        file.close()
    except:
        return 1
    return 0

# should not LATEX be in env?
#if WhereIs('dvips'):
#    latex = WhereIs('latex')
#else:
# latex = WhereIs('pdflatex')
bibtex = WhereIs('bibtex')
rerun = re.compile(r'\bRerun')

def latex2dvi(target=None,source=None,env=None):
    "Convert LaTeX to DVI/PDF"
    latex = env.get('latex',WhereIs('pdflatex'))
    tex = str(source[0])
    dvi = str(target[0])
    stem = re.sub('\.[^\.]+$','',dvi)    
    run = string.join([latex,tex],' ')
    # First latex run
    if os.system(run):
        return 1
    # Check if bibtex is needed
    aux = open(stem + '.aux',"r")    
    for line in aux.readlines():
        if re.search("bibdata",line):
            os.system(string.join([bibtex,stem],' '))
            os.system(run)
            os.system(run)
            break        
    aux.close()
    # (Add makeindex later)
    # Check if rerun is needed
    for i in range(3): # repeat 3 times at most
        done = 1
        log = open(stem + '.log',"r")
        for line in log.readlines():
            if rerun.search(line):
                done = 0
                break
        log.close()
        if done:
            break
        os.system(run)
    return 0

def retrieve(target=None,source=None,env=None):
    "Fetch data from the web"
    global rdatapath
    dir = env['dir']
    for file in map(str,target):
        urllib.urlretrieve(string.join([rdatapath,dir,file],os.sep),file)
    return 0

View = Builder(action = sep + "xtpen $SOURCES",src_suffix=vpsuffix)
# Klean = Builder(action = Action(clean,silent,['junk']))
Build = Builder(action = Action(pstexpen,varlist=['opts']),
                src_suffix=vpsuffix,suffix=pssuffix)
epstopdf = WhereIs('epstopdf')
if epstopdf:
    PDFBuild = Builder(action = epstopdf + " $SOURCES",
		       src_suffix=pssuffix,suffix='.pdf')
Retrieve = Builder(action = Action(retrieve,varlist=['dir']))

#if WhereIs('dvips'):
#    dvips = 1
#    Dvi = Builder(action = Action(latex2dvi),
#              src_suffix=['.tex','.ltx'],suffix='.dvi')
#    Ps = Builder(action = WhereIs('dvips') + " -Ppdf -G0 -o $TARGET $SOURCES",
#                 src_suffix='.dvi',suffix='.ps')
#    Pdf = Builder(action = WhereIs('ps2pdf') + " $SOURCES",
#                  src_suffix='.ps',suffix='.pdf')
#    ressuffix = '.ps'
#else:
dvips = 0
Pdf = Builder(action = Action(latex2dvi,varlist=['latex']),
              src_suffix=['.tex','.ltx'],suffix='.pdf')

acroread = WhereIs('acroread')
if acroread:
    Read = Builder(action = acroread + " $SOURCES",src_suffix='.pdf')
ressuffix = '.pdf'

fig2dev = WhereIs('fig2dev')
if fig2dev:
    XFig = Builder(action = fig2dev + ' -L pdf -p dummy $SOURCES $TARGETS',
                   suffix='.pdf',src_suffix='.fig')

#############################################################################
# CUSTOM SCANNERS
#############################################################################

isplot = None
def getplots(node,env,path):
    global isplot, ressufix
    if not isplot:
        isplot = re.compile(r'\\(?:side)?plot\s*\{([^\}]+)')
    contents = node.get_contents()
    plots = isplot.findall(contents)
    return map(lambda x: os.path.join(resdir,x) + ressuffix,plots)

Plots = Scanner(name='Plots',function=getplots,skeys=['.tex','.ltx'])

#############################################################################
# PLOTTING COMMANDS
#############################################################################

combine ={
    'SideBySideAniso': lambda n:
    sep + "vppen yscale=%d vpstyle=n gridnum=%d,1 $SOURCES" % (n,n),
    'OverUnderAniso': lambda n:
    sep + "vppen xscale=%d vpstyle=n gridnum=1,%d $SOURCES" % (n,n),
    'SideBySideIso': lambda n:
    sep + "vppen size=r vpstyle=n gridnum=%d,1 $SOURCES" % n,
    'OverUnderIso': lambda n:
    sep + "vppen size=r vpstyle=n gridnum=1,%d $SOURCES" % n,
    'TwoRows': lambda n:
    sep + "vppen size=r vpstyle=n gridnum=%d,2 $SOURCES" % (n/2),
    'Overlay': lambda n:
    sep + "vppen erase=o vpstyle=n $SOURCES",
    'Movie': lambda n:
    sep + "vppen vpstyle=n $SOURCES"
    }

#############################################################################

class Project(Environment):
    def __init__(self,**kw):
        apply(Environment.__init__,(self,),kw)
        # Add f90 later
        opts = Options(os.path.join(libdir,'rsfconfig.py'))
        rsfconf.options(opts)
        opts.Update(self)
        dir = os.path.basename(os.getcwd())
        self.path = datapath + dir + os.sep
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        self.Append(ENV={'DATAPATH':self.path,
                         'XAUTHORITY':
                         os.path.join(os.environ.get('HOME'),'.Xauthority'),
                         'DISPLAY': os.environ.get('DISPLAY'),
                         'VPLOTFONTDIR': os.environ.get('VPLOTFONTDIR'),
                         'RSFROOT':top},
                    BUILDERS={'View':View,
                              'Build':Build,
                              'Retrieve':Retrieve},
                    SCANNERS=[Plots],
                    LIBPATH=[libdir],
                    CPPPATH=[incdir],
                    LIBS=['rsf','m'],
                    PROGSUFFIX='.exe')
	if acroread:
	    self.Append(BUILDERS={'Read':Read})
	if epstopdf:
	    self.Append(BUILDERS={'PDFBuild':PDFBuild})
        if fig2dev:
            self.Append(BUILDERS={'XFig':XFig})
        self['PROGPREFIX']=''
        self.view = []
        self.figs = []
        self.pdfs = []
        self.coms = []
    def Exe(self,source,**kw):
         target = source.replace('.c','.exe')
         return apply(self.Program,(target,source),kw)
    def Flow(self,target,source,flow,stdout=1,stdin=1,
             suffix=sfsuffix,prefix=sfprefix,src_suffix=sfsuffix):
        if not flow:
            return None        
        sources = []
        if source:
            if type(source) is types.ListType:
                files = source
            else:
                files = string.split(source)
            for file in files:
                if ('.' not in file):
                    file = file + src_suffix
                sources.append(file)
        else:
            stdin=0
        lines = string.split(flow,';')
        steps = []
        for line in lines:
            substeps = []
            sublines = string.split(line,'|')
            for subline in sublines:           
                pars = string.split(subline)
                # command is assumed to be always first in line
                command = pars.pop(0)
                # check if this command is in our list
                rsfprog = prefix + command            
                if rsfdoc.progs.has_key(rsfprog):
                    command = os.path.join(bindir,rsfprog)
                    sources.append(command)
                    if record and (rsfprog not in self.coms):
                        self.coms.append(rsfprog)
                elif re.match(r'[^/]+\.exe$',command): # local program
                    command = os.path.join('.',command)                    
                #<- check for par files and add to the sources
                for par in pars:
                    if re.match("^par=",par):
                        sources.append(File(par[4:]))
                #<<- assemble the command line
                pars.insert(0,command)
                substeps.append(string.join(pars,' '))
            #<-
            steps.append(string.join(substeps," | "))
        #<- assemble the pipeline
        command = string.join(steps," ;\n")
        if stdout==1:
            command = command + " > $TARGET"
        elif stdout==0:
            command = command + " >/dev/null"
        if stdin:
            command = "< $SOURCE " + command
        targets = []
        if type(target) is types.ListType:
            files = target
        else:
            files = string.split(target)
        for file in files:
            if not re.search(suffix + '$',file):
                file = file + suffix
            targets.append(file)
        if suffix == sfsuffix:            
            datafiles = [] 
            for target in targets:
                if os.sep not in target:
                    datafile = self.path + target + '@'
                    datafiles.append(datafile)
            targets = targets + datafiles
        return self.Command(targets,sources,command)
    def Plot (self,target,source,flow,suffix=vpsuffix,vppen=None,**kw):
        if combine.has_key(flow):
            if not type(source) is types.ListType:
                source = string.split(source)
            flow = apply(combine[flow],[len(source)])
            if vppen:
                flow = flow + ' ' + vppen
            kw.update({'src_suffix':vpsuffix,'stdin':0})
        kw.update({'suffix':suffix})
        return apply(self.Flow,(target,source,flow),kw)
    def Result(self,target,source,flow,suffix=vpsuffix,
               pstexpen=None,**kw):
        target2 = os.path.join(resdir,target)
        if flow:
            plot = apply(self.Plot,(target2,source,flow),kw)
            self.Default (plot)
            self.view.append(self.View(target + '.view',plot))
            build = self.Build(target2 + pssuffix,plot,opts=pstexpen)
            self.figs.append(build)
            self.Alias(target + '.build',build)
        else:
            plot = None
            build = target2 + pssuffix
	if epstopdf:
	    buildPDF = self.PDFBuild(target2,build)
	    self.pdfs.append(buildPDF)
	    self.Alias(target + '.buildPDF',buildPDF)
        return plot
    def End(self):
        self.Alias('view',self.view)
        if self.figs: # if any results
            build = self.Alias('build',self.figs)
        if self.pdfs:
            buildPDF = self.Alias('buildPDF',self.pdfs)
        self.Append(BUILDERS={'Pdf':Pdf})
        if os.path.isfile('paper.tex'): # if there is a paper
            if dvips:
                self.paper = self.Dvi(target='paper',source='paper.tex')
                self.Alias('dvi',self.paper)
                self.Alias('ps',self.Ps('paper'))
                self.Alias('pdf',self.Pdf('paper'))
            else:
                self.paper = self.Pdf(target='paper',source='paper.tex')
                self.Alias('pdf',self.paper)
            self.paper.target_scanner = Plots
	    if acroread:
		self.Alias('read',self.Read('paper'))
        if record:
            self.Command('.sf_uses',None,'echo %s' %
                         string.join(self.coms,' '))
    def Fetch(self,file,dir):
        return self.Retrieve(file,None,dir=dir)

# Default project
project = Project()
def Flow(target,source,flow,**kw):
    return apply(project.Flow,(target,source,flow),kw)
def Plot (target,source,flow,**kw):
    return apply(project.Plot,(target,source,flow),kw)
def Result(target,source,flow,**kw):
    return apply(project.Result,(target,source,flow),kw)
def Fetch(file,dir):
    return project.Fetch(file,dir)
def XFig(file):
    return project.XFig(os.path.join(resdir,file),file)
def Exe(source,**kw):
     return apply(project.Exe,[source],kw)
def End():
    project.End()

if __name__ == "__main__":
     import pydoc
     pydoc.help(Project)
     
# 	$Id: rsfproj.py,v 1.34 2004/06/18 01:06:44 fomels Exp $	
