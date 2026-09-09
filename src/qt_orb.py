"""Fast Qt recorder overlay that never steals keyboard focus."""
import math
import time
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QPainterPath, QPen, QRadialGradient
from PySide6.QtWidgets import QWidget

class ReactiveOrb(QWidget):
    def __init__(self, size=64, parent=None):
        super().__init__(parent); self.size=size; self.level=0.; self.target_level=0.; self.phase=0.; self._last=time.perf_counter()
        self.setFixedSize(size,size); self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.timer=QTimer(self); self.timer.setTimerType(Qt.TimerType.PreciseTimer); self.timer.timeout.connect(self._tick)
    def set_volume(self,rms): self.target_level=min(1.,math.sqrt(max(0.,(float(rms)-45.)/2200.)))
    def start(self):
        self._last=time.perf_counter()
        if not self.timer.isActive(): self.timer.start(20)
        self.update()
    def stop(self): self.timer.stop(); self.target_level=0.
    def _tick(self):
        now=time.perf_counter(); dt=min(.08,now-self._last); self._last=now; speed=22. if self.target_level>self.level else 9.
        self.level+=(self.target_level-self.level)*(1.-math.exp(-dt*speed)); self.phase+=dt*(.8+3.6*self.level); self.update()
    def paintEvent(self,event):
        del event; p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); r=QRectF(3,3,self.width()-6,self.height()-6); c=r.center(); rad=r.width()/2
        clip=QPainterPath(); clip.addEllipse(r); p.setClipPath(clip)
        base=QRadialGradient(QPointF(c.x()-rad*.3,c.y()-rad*.35),rad*1.35); base.setColorAt(0,QColor('#6828FF')); base.setColorAt(.43,QColor('#154BFF')); base.setColorAt(1,QColor('#02D8CF')); p.setPen(Qt.PenStyle.NoPen); p.setBrush(base); p.drawEllipse(r)
        y=c.y()+math.sin(self.phase*2.2)*rad*.12; wave=QPainterPath(); wave.moveTo(-4,y); wave.cubicTo(rad*.55,y-rad*(.5+self.level*.2),rad*1.25,y+rad*(.42+self.level*.18),self.width()+4,y-rad*.16); wave.lineTo(self.width()+4,self.height()+4); wave.lineTo(-4,self.height()+4); wave.closeSubpath(); p.setOpacity(.48); p.setBrush(QColor('#08E4D1')); p.drawPath(wave)
        p.setClipping(False); p.setOpacity(1); p.setPen(QPen(QColor(72,122,255,180),1.5)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawEllipse(r); p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(255,255,255,65)); p.drawEllipse(QRectF(rad*.48,rad*.36,rad*.28,rad*.14))

class OrbOverlay(QWidget):
    def __init__(self,size=64):
        flags=Qt.WindowType.FramelessWindowHint|Qt.WindowType.Tool|Qt.WindowType.WindowStaysOnTopHint|Qt.WindowType.WindowDoesNotAcceptFocus
        super().__init__(None,flags); self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground); self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating); self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setWindowTitle('ALTWISP recorder')
        self.orb=ReactiveOrb(size,self); self.setFixedSize(size,size); area=QGuiApplication.primaryScreen().availableGeometry(); self.move(area.center().x()-size//2,area.bottom()-size-28); self.hide()
    def show_orb(self): self.show(); self.raise_(); self.orb.start()
    def hide_orb(self): self.hide(); self.orb.stop()
