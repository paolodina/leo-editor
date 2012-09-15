#@+leo-ver=5-thin
#@+node:ekr.20120913110135.10579: * @file screencast.py
#@+<< docstring >>
#@+node:ekr.20120913110135.10589: ** << docstring >>
'''Screencast tools for Leo.

Injects c.screencast_controller ivar into all commanders.
'''
#@-<< docstring >>
#@+<< imports >>
#@+node:ekr.20120913110135.10590: ** << imports >>
import random

import leo.core.leoGlobals as g
import leo.core.leoGui as leoGui # for leoKeyEvents.

# import PyQt4.Qt as Qt
import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui
#@-<< imports >>

# To do:
# Typing in minibuffer. For example, demo search commands and typing completion.s

#@@language python
#@@tabwidth -4

#@+others
#@+node:ekr.20120913110135.10608: ** top-level
#@+node:ekr.20120913110135.10603: *3* init
def init ():
        
    ok = g.app.gui.guiName() in ('qt','qttabs')

    if ok:
        g.registerHandler('after-create-leo-frame',onCreate)
        g.plugin_signon(__name__)

    return ok
#@+node:ekr.20120913110135.10604: *3* onCreate
def onCreate (tag, keys):
    
    '''Inject c.screenshot_controller into the commander.'''
    
    c = keys.get('c')
    if c:
        c.screencast_controller = scc = ScreenCastController(c)
#@+node:ekr.20120913110135.10607: ** class ScreenCastController
class ScreenCastController:
    
    #@+others
    #@+node:ekr.20120913110135.10606: *3* __init__ (ScreenCastController)
    def __init__(self,c):
        
        self.c = c
        self.log_color = 'black'
        self.log_focus = True # True: writing to log sets focus to log.
        self.ignore_keys = False # True: ignore keys in state_handler.
        self.in_minibuffer = False # True: simulating minibuffer
        self.manual = True # True: transition manually between scenes.
        self.n1 = 0.02 # default minimal typing delay.
        self.n2 = 0.175 # default maximum typing delay.
        self.p1 = None # The first slide of the show.
        self.p = None # The present slide of the show.
        self.speed = 1.0 # Amount to multiply wait times.
        self.node_stack = [] # For undo.
        self.widgets = [] # List of (popup) widgets created by this class.
        
        # inject c.screenCastController
        c.screenCastController = self
    #@+node:ekr.20120913110135.10580: *3* body_keys
    def body_keys (self,s,n1=None,n2=None):
        
        '''Simulate typing in the body pane.
        n1 and n2 indicate the range of delays between keystrokes.
        '''
        
        m = self ; c = m.c
        if n1 is None: n1 = m.n1
        if n2 is None: n2 = m.n2
        c.bodyWantsFocusNow()
        p = c.p
        w = c.frame.body.bodyCtrl.widget
        c.undoer.setUndoTypingParams(p,'typing',
            oldText=p.b,newText=p.b+s,oldSel=None,newSel=None,oldYview=None)
        for ch in s:
            p.b = p.b + ch
            w.repaint()
            m.wait(n1,n2,force=True)
        c.redraw()
    #@+node:ekr.20120914133947.10578: *3* caption
    def caption (self,pane,s,center=False):
        
        '''Pop up a QPlainTextEdit in the indicated pane.'''
        
        m = self
        parent = m.pane_widget(pane)
        if parent:
            s = s.rstrip()
            if s and s[-1].isalpha(): s = s+'.'
            w = QtGui.QPlainTextEdit(s,parent)
            w.setObjectName('screencastcaption')
            m.widgets.append(w)
            w2 = m.pane_widget(pane)
            geom = w2.geometry()
            w.resize(geom.width(),min(100,geom.height()/2))
            # w.setContentsMargins(5,5,5,5)
            off = QtCore.Qt.ScrollBarAlwaysOff
            w.setHorizontalScrollBarPolicy(off)
            w.setVerticalScrollBarPolicy(off)
            font = w.font()
            font.setPointSize(18)
            w.setFont(font)
            w.show()
            return w
        else:
            g.trace('bad pane: %s' % (pane))
            return None
    #@+node:ekr.20120913110135.10612: *3* clear_log (not used)
    def clear_log (self):
        
        '''Clear the log.'''

        m = self
        m.c.frame.log.clearTab('Log')
    #@+node:ekr.20120913110135.10581: *3* command
    def command(self,command_name):
        
        '''Execute the command whose name is given and update the screen immediately.'''

        m = self ; c = m.c

        c.k.simulateCommand(command_name)
            # Named commands handle their own undo!
            # The undo handling in m.next should suffice.

        c.redraw_now()
        m.repaint('all')
    #@+node:ekr.20120914163440.10581: *3* delete_widgets
    def delete_widgets (self):
        
        m = self

        for w in m.widgets:
            w.deleteLater()

        m.widgets=[]
    #@+node:ekr.20120915091327.13816: *3* find_screencast
    def find_screencast(self,p):
        
        m,p,p1,tag = self,p.copy(),p.copy(),'@screencast'
        
        while p:
            if p.h.startswith(tag):
                return p
            else:
                p.moveToThreadNext()

        p = p1.threadBack()
        while p:
            if p.h.startswith(tag):
                return p
            else:
                p.moveToThreadBack()
        
        g.es_print('no @screencast node found')
        return None
    #@+node:ekr.20120913110135.10582: *3* focus
    def focus(self,pane):
        
        '''Immediately set the focus to the given pane.'''

        m = self ; c = m.c
        d = {
            'body': c.bodyWantsFocus,
            'log':  c.logWantsFocus,
            'tree': c.treeWantsFocus,
        }
        
        f = d.get(pane)
        if f:
            f()
            c.outerUpdate()
            m.repaint(pane)
        else:
            g.trace('bad pane: %s' % (pane))
    #@+node:ekr.20120913110135.10583: *3* head_keys
    def head_keys(self,s,n1=None,n2=None):
        
        '''Simulate typing in the headline.
        n1 and n2 indicate the range of delays between keystrokes.
        '''
        
        m = self ; c = m.c ; p = c.p ; undoType = 'Typing'
        oldHead = p.h ; tree = c.frame.tree
        if n1 is None: n1 = m.n1
        if n2 is None: n2 = m.n2
        p.h=''
        c.editHeadline()
        w = tree.edit_widget(p)
        # Support undo.
        undoData = c.undoer.beforeChangeNodeContents(p,oldHead=oldHead)
        dirtyVnodeList = p.setDirty()
        c.undoer.afterChangeNodeContents(p,undoType,undoData,
            dirtyVnodeList=dirtyVnodeList)
        # Lock out key handling in m.state_handler.
        m.ignore_keys = True
        try:
            for ch in s:
                p.h = p.h + ch
                tree.repaint() # *not* tree.update.
                m.wait(n1,n2,force=True)
                event = leoGui.leoKeyEvent(c,ch,ch,w,x=0,y=0,x_root=0,y_root=0)
                c.k.masterKeyHandler(event)
        finally:
            m.ignore_keys = False
        p.h=s
        c.redraw()
    #@+node:ekr.20120913110135.10615: *3* image
    def image(self,pane,fn,center=None,height=None,width=None):
        
        '''Put an image in the indicated pane.'''

        m = self
        parent = m.pane_widget(pane)
        if parent:
            w = QtGui.QLabel('label',parent)
            fn = m.resolve_icon_fn(fn)
            if not fn: return None
            pixmap = QtGui.QPixmap(fn)
            if not pixmap:
                return g.trace('Not a pixmap: %s' % (fn))
            if height:
                pixmap = pixmap.scaledToHeight(height)
            if width:
                pixmap = pixmap.scaledToWidth(width)
            w.setPixmap(pixmap)
            if center:
                g_w=w.geometry()
                g_p=parent.geometry()
                dx = (g_p.width()-g_w.width())/2
                w.move(g_w.x()+dx,g_w.y()+10)
            w.show()
            m.widgets.append(w)
            return w
        else:
            g.trace('bad pane: %s' % (pane))
            return None

        
    #@+node:ekr.20120913110135.10584: *3* key
    def key(self,setting,command):

        '''Simulate hitting the key.  Show the key in the log pane.'''

        m = self ; c = m.c ; k = c.k

        stroke = c.k.strokeFromSetting(setting)
        k.simulateCommand(command)
        c.redraw()
        m.repaint('all')
    #@+node:ekr.20120913110135.10610: *3* log
    def log(self,s,begin=False,end=False,image_fn=None,pane='log'):
        
        '''Put a message to the log pane, highlight it, and pause.'''
        
        m = self

        if not begin:
            m.wait(1)
            
        m.caption(pane,s)
        m.repaint('all')
        
        if not end:
            m.wait(1)
        
        
    #@+node:ekr.20120915091327.13817: *3* minibuffer_keys
    def minibuffer_keys (self,s,n1=None,n2=None):
        
        '''Simulate typing in the minibuffer.
        n1 and n2 indicate the range of delays between keystrokes.
        '''
        
        m = self ; c = m.c ; tree = c.frame.tree

        if n1 is None: n1 = m.n1
        if n2 is None: n2 = m.n2
        try:
            m.in_minibuffer = True
            c.minibufferWantsFocus()
            c.outerUpdate()
            for ch in s:
                tree.repaint() # *not* tree.update.
                m.wait(n1,n2,force=True)
                event = leoGui.leoKeyEvent(c,ch,ch,w=tree,x=0,y=0,x_root=0,y_root=0)
                c.k.masterKeyHandler(event)
        finally:
            m.in_minibuffer = False

        c.redraw_now() # Sets focus.
        c.widgetWantsFocusNow(c.frame.miniBufferWidget.widget)
        c.outerUpdate()
    #@+node:ekr.20120914074855.10721: *3* next
    def next (self):
        
        '''Find the next screencast node and execute its script.
        Call m.quit if no more nodes remain.'''
        
        trace = False and not g.unitTesting
        m = self ; c = m.c
        m.delete_widgets()
        while m.p:
            if trace: g.trace(m.p.h)
            h = m.p.h.replace('_','').replace('-','')
            if g.match_word(h,0,'@ignore'):
                m.p.moveToThreadNext()
            elif g.match_word(h,0,'@ignoretree'):
                m.p.moveToNodeAfterTree()
            else:
                p2 = m.p.copy()
                m.p.moveToThreadNext()
                if p2.b.strip():
                    if trace: g.trace(p2.h,c.p.v)
                    d = {'c':c,'g:':g,'m':m,'p':p2}
                    tag = 'screencast'
                    m.node_stack.append(p2)
                    undoData = c.undoer.beforeChangeGroup(c.p,tag,verboseUndoGroup=False)
                    c.executeScript(p=p2,namespace=d,useSelectedText=False)
                    c.undoer.afterChangeGroup(c.p,tag,undoData)
                    if m.p: return
        # No m.p or no new node found.
        m.quit()
    #@+node:ekr.20120914133947.10579: *3* pane_widget
    def pane_widget (self,pane):
        
        '''Return the pane's widget.'''
        
        m = self ; c = m.c

        d = {
            'all':  c.frame.top,
            'body': c.frame.body.bodyCtrl.widget,
            'log':  c.frame.log.logCtrl.widget,
            'tree': c.frame.tree.treeWidget,
        }

        return d.get(pane)
    #@+node:ekr.20120914074855.10722: *3* quit
    def quit (self):
        
        '''Terminate the slide show.'''
        
        m = self
        print('end slide show: %s' % (m.p1.h))
        g.es('end slide show',color='red')
        m.delete_widgets()
        m.c.k.keyboardQuit()
    #@+node:ekr.20120913110135.10585: *3* repaint
    def repaint(self,pane):
        
        '''Repaint the given pane.'''

        m = self
        w = m.pane_widget(pane)
        if w:
            w.repaint()
        else:
            g.trace('bad pane: %s' % (pane))
    #@+node:ekr.20120914163440.10582: *3* resolve_icon_fn
    def resolve_icon_fn (self,fn):
        
        '''Resolve fn relative to the Icons directory.'''
        
        m = self

        dir_ = g.os_path_finalize_join(g.app.loadDir,'..','Icons')
        path = g.os_path_finalize_join(dir_,fn)
        
        if g.os_path_exists(path):
            return path
        else:
            g.trace('does not exist: %s' % (path))
            return None
    #@+node:ekr.20120913110135.10611: *3* set_log_focus & set_speed
    def set_log_focus(self,val):
        
        '''Set m.log_focus to the given value.'''

        m = self
        m.log_focus = bool(val)

    def set_speed (self,speed):
        
        '''Set m.speed to the given value.'''
        
        m = self
        if speed < 0:
            g.trace('speed must be >= 0.0')
        else:
            m.speed = speed
    #@+node:ekr.20120914074855.10720: *3* start
    def start (self,p,manual=True):
        
        '''Start a screencast whose root node is p.
        
        Important: p is not necessarily c.p!
        '''
        
        m = self ; c = m.c
        
        # Set ivars
        m.manual=manual
        m.n1 = 0.02 # default minimal typing delay.
        m.n2 = 0.175 # default maximum typing delay.
        m.p1 = p.copy()
        m.p = p.copy()

        p.contract()
        c.redraw_now(p)
        m.delete_widgets()
            # Clear widgets left over from previous, unfinished, slideshows.
        m.state_handler()
    #@+node:ekr.20120914074855.10715: *3* state_handler
    def state_handler (self,event=None):
        
        '''Handle keys while in the "screencast" input state.'''

        trace = False and not g.unitTesting
        m = self ; c = m.c ; k = c.k ; tag = 'screencast'
        state = k.getState(tag)
        char = event and event.char or ''
        if trace: g.trace('state: %s char: %s' % (state,char))
        if m.ignore_keys:
            return
        if state == 0:
            assert m.p1 and m.p1 == m.p
            # Init the minibuffer as in k.fullCommand.
            k.mb_event = event
            k.mb_prefix = k.getLabel()
            k.mb_prompt = 'Screencast: '
            k.mb_tabList = []
            k.setLabel(k.mb_prompt)
            k.setState(tag,1,m.state_handler)
            m.next()
        elif char == 'Escape': # k.masterKeyHandler handles ctrl-g.
            m.quit()
        elif char == 'Right':
            m.next()
        elif char == 'Left':
            m.undo()
        elif m.in_minibuffer:
            # Similar to code in k.fullCommand
            if char in ('\b','BackSpace'):
                k.doBackSpace(list(c.commandsDict.keys()))
            elif char in ('\t','Tab'):
                aList = list(c.commandsDict.keys())
                aList = [z for z in aList if z.startswith('ins')]
                k.doTabCompletion(aList,allow_empty_completion=True)
            elif char in ('\n','Return'):
                c.frame.log.deleteTab('Completion')
                k.callAltXFunction(k.mb_event)
                k.setState(tag,1,m.state_handler) # Stay in the slideshow!
            else:
                event = g.bunch(char=char)
                k.mb_tabList = []
                k.updateLabel(event)
                k.mb_tabListPrefix = k.getLabel()
            c.minibufferWantsFocus()
        else:
            if trace: g.trace('ignore %s' % (char))
    #@+node:ekr.20120914195404.11208: *3* undo
    def undo (self):
        
        '''Undo the previous screencast scene.'''

        m = self
        
        m.delete_widgets()
        
        if m.node_stack:
            c = m.c
            m.p = m.node_stack.pop()
            c.undoer.undo()
            c.redraw()
        else:
            m.quit()
            # g.trace('can not undo')
    #@+node:ekr.20120913110135.10587: *3* wait
    def wait(self,n=1,high=0,force=False):
        
        '''Wait for an interval between n and high.
        Do nothing if in manual mode unless force is True.'''
        
        m = self
        
        if m.manual and not force:
            return

        if n > 0 and high > 0:
            n = random.uniform(n,n+high)

        if n > 0:
            n = n * m.speed
            # g.trace(n)
            g.sleep(n)
    #@-others
#@-others
#@-leo