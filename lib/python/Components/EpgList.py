from HTMLComponent import HTMLComponent
from GUIComponent import GUIComponent

from enigma import eEPGCache, eListbox, eListboxPythonMultiContent, gFont, \
	RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER

from Tools.LoadPixmap import LoadPixmap

from time import localtime, time
from Components.config import config
from ServiceReference import ServiceReference
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
import skin

EPG_TYPE_SINGLE = 0
EPG_TYPE_MULTI = 1
EPG_TYPE_SIMILAR = 2
EPG_TYPE_EPGBAR = 3

class Rect:
	def __init__(self, x, y, width, height):
		self.__left = x
		self.__top = y
		self.__width = width
		self.__height = height

	def left(self):
		return self.__left

	def top(self):
		return self.__top

	def height(self):
		return self.__height

	def width(self):
		return self.__width

class EPGList(HTMLComponent, GUIComponent):
	def __init__(self, type=EPG_TYPE_SINGLE, selChangedCB=None, timer = None):
		self.days = (_("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat"), _("Sun"))
		self.timer = timer
		self.onSelChanged = [ ]
		if selChangedCB is not None:
			self.onSelChanged.append(selChangedCB)
		GUIComponent.__init__(self)
		self.type=type
		self.l = eListboxPythonMultiContent()
		font, size = skin.parameters.get("EPGlistFont1", ('Regular',22))
		self.l.setFont(0, gFont(font, size))
		font, size = skin.parameters.get("EPGlistFont2", ('Regular',16))
		self.l.setFont(1, gFont(font, size))
		if type == EPG_TYPE_SINGLE:
			self.l.setBuildFunc(self.buildSingleEntry)
		elif type == EPG_TYPE_MULTI:
			self.l.setBuildFunc(self.buildMultiEntry)
		elif type == EPG_TYPE_EPGBAR:
			self.l.setBuildFunc(self.buildEPGBarEntry)
		else:
			assert(type == EPG_TYPE_SIMILAR)
			self.l.setBuildFunc(self.buildSimilarEntry)
		self.epgcache = eEPGCache.getInstance()
		self.clock_pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, 'skin_default/icons/epgclock.png'))
		self.clock_add_pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, 'skin_default/icons/epgclock_add.png'))
		self.clock_pre_pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, 'skin_default/icons/epgclock_pre.png'))
		self.clock_post_pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, 'skin_default/icons/epgclock_post.png'))
		self.clock_prepost_pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, 'skin_default/icons/epgclock_prepost.png'))

		self.clock_pixmap_disabled = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, 'skin_default/icons/epgclock_disabled.png'))

	def getEventFromId(self, service, eventid):
		event = None
		if self.epgcache is not None and eventid is not None:
			event = self.epgcache.lookupEventId(service.ref, eventid)
		return event

	def getCurrentChangeCount(self):
		if self.type == EPG_TYPE_MULTI and self.l.getCurrentSelection() is not None:
			return self.l.getCurrentSelection()[0]
		return 0

	def getCurrent(self):
		idx=0
		if self.type == EPG_TYPE_MULTI:
			idx += 1
		tmp = self.l.getCurrentSelection()
		if tmp is None:
			return ( None, None )
		eventid = tmp[idx+1]
		service = ServiceReference(tmp[idx])
		event = self.getEventFromId(service, eventid)
		return ( event, service )

	def moveUp(self):
		self.instance.moveSelection(self.instance.moveUp)

	def moveDown(self):
		self.instance.moveSelection(self.instance.moveDown)

	def connectSelectionChanged(func):
		if not self.onSelChanged.count(func):
			self.onSelChanged.append(func)

	def disconnectSelectionChanged(func):
		self.onSelChanged.remove(func)

	def selectionChanged(self):
		for x in self.onSelChanged:
			if x is not None:
				x()
#				try:
#					x()
#				except: # FIXME!!!
#					print "FIXME in EPGList.selectionChanged"
#					pass

	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		instance.setWrapAround(True)
		instance.selectionChanged.get().append(self.selectionChanged)
		instance.setContent(self.l)

	def preWidgetRemove(self, instance):
		instance.selectionChanged.get().remove(self.selectionChanged)
		instance.setContent(None)

	def reload(self):
		self.l.setList(self.list)

	def recalcEntrySize(self):
		esize = self.l.getItemSize()
		width = esize.width()
		height = esize.height()
		if self.type == EPG_TYPE_SINGLE:
			self.weekday_rect = Rect(0, 0, width/20*2-10, height)
			self.datetime_rect = Rect(width/20*2, 0, width/20*5-15, height)
			self.descr_rect = Rect(width/20*7, 0, width/20*13, height)
		elif self.type == EPG_TYPE_EPGBAR:
			self.rec_size = Rect(0, 0, width, height)
		elif self.type == EPG_TYPE_MULTI:
			xpos = 0;
			w = width/10*3;
			self.service_rect = Rect(xpos, 0, w-10, height)
			xpos += w;
			w = width/10*2;
			self.start_end_rect = Rect(xpos, 0, w-10, height)
			self.progress_rect = Rect(xpos, 4, w-10, height-8)
			xpos += w
			w = width/10*5;
			self.descr_rect = Rect(xpos, 0, width, height)
		else: # EPG_TYPE_SIMILAR
			self.weekday_rect = Rect(0, 0, width/20*2-10, height)
			self.datetime_rect = Rect(width/20*2, 0, width/20*5-15, height)
			self.service_rect = Rect(width/20*7, 0, width/20*13, height)

	def getClockPixmap(self, refstr, beginTime, duration, eventId):
		pre_clock = 1
		post_clock = 2
		clock_type = 0
		endTime = beginTime + duration
		for x in self.timer.timer_list:
			if x.service_ref.ref.toString() == refstr:
				if x.eit == eventId:
					return self.clock_pixmap
				beg = x.begin
				end = x.end
				if beginTime > beg and beginTime < end and endTime > end:
					clock_type |= pre_clock
				elif beginTime < beg and endTime > beg and endTime < end:
					clock_type |= post_clock
		if clock_type == 0:
			return self.clock_add_pixmap
		elif clock_type == pre_clock:
			return self.clock_pre_pixmap
		elif clock_type == post_clock:
			return self.clock_post_pixmap
		else:
			return self.clock_prepost_pixmap

	def getPixmapForEntry(self, service, eventId, beginTime, duration):
		rec=beginTime and (self.timer.isInTimer(eventId, beginTime, duration, service))
		if rec:
			clock_pic = self.getClockPixmap(service, beginTime, duration, eventId)
		else:
			clock_pic = None

		if clock_pic is not self.clock_pixmap:
			for timer in self.timer.processed_timers:
				if timer.eit == eventId and timer.service_ref.ref.toString() == str(service) and timer.disabled == True:
					clock_pic = self.clock_pixmap_disabled
					rec = beginTime
					break
		return (clock_pic, rec)

	def buildSingleEntry(self, service, eventId, beginTime, duration, EventName):
		(clock_pic, rec) = self.getPixmapForEntry(service, eventId, beginTime, duration)
		r1=self.weekday_rect
		r2=self.datetime_rect
		r3=self.descr_rect
		t = localtime(beginTime)
		x1,y1,w1,h1 = skin.parameters.get("EPGlistText1", (r1.left(), r1.top(), r1.width(), r1.height()))
		x2,y2,w2,h2 = skin.parameters.get("EPGlistText2", (r2.left(), r2.top(), r2.width(), r2.height()))
		res = [
			None, # no private data needed
			(eListboxPythonMultiContent.TYPE_TEXT, x1, y1, w1, h1, 0, RT_HALIGN_RIGHT, self.days[t[6]]),
			(eListboxPythonMultiContent.TYPE_TEXT, x2, y2, w2, h2, 0, RT_HALIGN_RIGHT, "%02d.%02d.  %02d:%02d"%(t[2],t[1],t[3],t[4]))
		]

		if rec:
			x3,y3,w3,h3 = skin.parameters.get("EPGlistRecImage", (r3.left(), r3.top(), 21, 21))
			x4,y4,w4,h4 = skin.parameters.get("EPGlistRecText", (r3.left() + 25, r3.top(), r3.width(), r3.height()))
			res.extend((
					(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, x3, y3, w3, h3, clock_pic),
					(eListboxPythonMultiContent.TYPE_TEXT, x4, y4, w4, h4, 0, RT_HALIGN_LEFT, EventName)
				))
		else:
			x3,y3,w3,h3 = skin.parameters.get("EPGlistNonRecText", (r3.left(), r3.top(), r3.width(), r3.height()))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, x3, y3, w3, h3, 0, RT_HALIGN_LEFT, EventName))
		return res

	def buildSimilarEntry(self, service, eventId, beginTime, service_name, duration):
		(clock_pic, rec) = self.getPixmapForEntry(service, eventId, beginTime, duration)
		r1=self.weekday_rect
		r2=self.datetime_rect
		r3=self.service_rect
		t = localtime(beginTime)
		x1,y1,w1,h1 = skin.parameters.get("EPGlistSimilarText1", (r1.left(), r1.top(), r1.width(), r1.height()))
		x2,y2,w2,h2 = skin.parameters.get("EPGlistSimilarText2", (r2.left(), r2.top(), r2.width(), r2.height()))
		res = [
			None,  # no private data needed
			(eListboxPythonMultiContent.TYPE_TEXT, x1, y1, w1, h1, 0, RT_HALIGN_RIGHT, self.days[t[6]]),
			(eListboxPythonMultiContent.TYPE_TEXT, x2, y2, w2, h2, 0, RT_HALIGN_RIGHT, "%02d.%02d, %02d:%02d"%(t[2],t[1],t[3],t[4]))
		]
		if rec:
			x1,y1,w1,h1 = skin.parameters.get("EPGlistSimilarRecIcon", (r3.left(), r3.top(), 21,21))
			x2,y2,w2,h2 = skin.parameters.get("EPGlistSimilarRecText", (r3.left() + 25, r3.top(), r3.width(), r3.height()))
			res.extend((
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, x1, y1, w1, h1, clock_pic),
				(eListboxPythonMultiContent.TYPE_TEXT, x2, y2, w2, h2, 0, RT_HALIGN_LEFT, service_name)
			))
		else:
			x1,y1,w1,h1 = skin.parameters.get("EPGlistSimilarNonRecText", (r3.left(), r3.top(), r3.width(), r3.height()))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, x1, y1, w1, h1, 0, RT_HALIGN_LEFT, service_name))
		return res

	def buildMultiEntry(self, changecount, service, eventId, beginTime, duration, EventName, nowTime, service_name):
		(clock_pic, rec) = self.getPixmapForEntry(service, eventId, beginTime, duration)
		r1=self.service_rect
		r2=self.progress_rect
		r3=self.descr_rect
		r4=self.start_end_rect
		res = [ None ] # no private data needed
		if rec:
			x1,y1,w1,h1 = skin.parameters.get("EPGlistMultiRecText", (r1.left(), r1.top(), r1.width() - 21, r1.height()))
			x2,y2,w2,h2 = skin.parameters.get("EPGlistMultiRecIcon", (r1.left() + r1.width() - 16, r1.top(), 21, 21))
			res.extend((
				(eListboxPythonMultiContent.TYPE_TEXT, x1, y1, w1, h1, 0, RT_HALIGN_LEFT, service_name),
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, x2, y2, w2, h2, clock_pic)
			))
		else:
			x1,y1,w1,h1 = skin.parameters.get("EPGlistMultiNonRecText", (r1.left(), r1.top(), r1.width(), r1.height()))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, x1, y1, w1, h1, 0, RT_HALIGN_LEFT, service_name))
		if beginTime is not None:
			if nowTime < beginTime:
				begin = localtime(beginTime)
				end = localtime(beginTime+duration)
				x1,y1,w1,h1 = skin.parameters.get("EPGlistMultiBeginText1", (r4.left(), r4.top(), r4.width(), r4.height()))
				x2,y2,w2,h2 = skin.parameters.get("EPGlistMultiBeginText2", (r3.left(), r3.top(), r3.width(), r3.height()))
#				print "begin", begin
#				print "end", end
				res.extend((
					(eListboxPythonMultiContent.TYPE_TEXT, x1, y1, w1, h1, 1, RT_HALIGN_CENTER|RT_VALIGN_CENTER, "%02d.%02d - %02d.%02d"%(begin[3],begin[4],end[3],end[4])),
					(eListboxPythonMultiContent.TYPE_TEXT, x2, y2, w2, h2, 0, RT_HALIGN_LEFT, EventName)
				))
			else:
				x1,y1,w1,h1 = skin.parameters.get("EPGlistMultiProgress", (r2.left(), r2.top(), r2.width(), r2.height()))
				x2,y2,w2,h2 = skin.parameters.get("EPGlistMultiProgressText", (r3.left(), r3.top(), r3.width(), r3.height()))
				percent = (nowTime - beginTime) * 100 / duration
				res.extend((
					(eListboxPythonMultiContent.TYPE_PROGRESS, x1, y1, w1, h1, percent),
					(eListboxPythonMultiContent.TYPE_TEXT, x2, y2, w2, h2, 0, RT_HALIGN_LEFT, EventName)
				))
		return res

	def buildEPGBarEntry(self, service, eventId, beginTime, duration, EventName, nowTime, service_name):
		(clock_pic, rec) = self.getPixmapForEntry(service, eventId, beginTime, duration)
		r0 = self.rec_size
		t = localtime(beginTime)
		begin = localtime(beginTime)
		end = localtime(beginTime+duration)

		dur = " (" + str(duration/60) + " " + _("min") + ")"
		from_to_str = " %02d:%02d - %02d:%02d " % (begin[3],begin[4],end[3],end[4])
		epg_str = self.days[t[6]] + from_to_str + EventName + dur

		res = [None]
		if rec:
			x1,y1,w1,h1 = skin.parameters.get("EPGlistEPGBarIcon", (5,0,21,21))
			x2,y2,w2,h2 = skin.parameters.get("EPGlistEPGBarText1", (30,0,r0.width() - 30, r0.height()))
			res.extend((
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, x1, y1, w1, h1, clock_pic),
				res.append((eListboxPythonMultiContent.TYPE_TEXT, x2, y2, w2, h2, 0, RT_HALIGN_LEFT, epg_str))
			))
		else:
			x1,y1,w1,h1 = skin.parameters.get("EPGlistEPGBarText2", (5, 0, r0.width() - 5, r0.height()))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, x1, y1, w1, h1, 0, RT_HALIGN_LEFT, epg_str))
		return res

	def queryEPG(self, list, buildFunc=None):
		if self.epgcache is not None:
			if buildFunc is not None:
				return self.epgcache.lookupEvent(list, buildFunc)
			else:
				return self.epgcache.lookupEvent(list)
		return [ ]

	def fillMultiEPG(self, services, stime=-1):
		#t = time()
		test = [ (service.ref.toString(), 0, stime) for service in services ]
		test.insert(0, 'X0RIBDTCn')
		self.list = self.queryEPG(test)
		self.l.setList(self.list)
		#print time() - t
		self.selectionChanged()

	def updateMultiEPG(self, direction):
		#t = time()
		test = [ x[3] and (x[1], direction, x[3]) or (x[1], direction, 0) for x in self.list ]
		test.insert(0, 'XRIBDTCn')
		tmp = self.queryEPG(test)
		cnt=0
		for x in tmp:
			changecount = self.list[cnt][0] + direction
			if changecount >= 0:
				if x[2] is not None:
					self.list[cnt]=(changecount, x[0], x[1], x[2], x[3], x[4], x[5], x[6])
			cnt+=1
		self.l.setList(self.list)
		#print time() - t
		self.selectionChanged()

	def fillSingleEPG(self, service):
		t = time()
		epgstarttime = t - int(config.usage.show_old_epg.value)
		test = [ 'RIBDT', (service.ref.toString(), 0, epgstarttime, -1) ]
		self.list = self.queryEPG(test)
		self.l.setList(self.list)
		if t != epgstarttime:
			print "[EPGView] select current service"
			idx = 0
			for x in self.list:
				idx += 1
				if t < x[2]+x[3]:
					break
			self.instance.moveSelectionTo(idx-1)
		self.selectionChanged()

	def fillEPGBar(self, service):
		t = time()
		test = [ 'RIBDTCn', (service.ref.toString(), 0, t, 1440) ]
		self.list = self.queryEPG(test)
		self.l.setList(self.list)
		self.instance.moveSelectionTo(0)
		self.selectionChanged()

	def sortSingleEPG(self, type):
		list = self.list
		if list:
			event_id = self.getSelectedEventId()
			if type == 1:
				list.sort(key=lambda x: (x[4] and x[4].lower(), x[2]))
			else:
				assert(type == 0)
				list.sort(key=lambda x: x[2])
			self.l.invalidate()
			self.moveToEventId(event_id)

	def getSelectedEventId(self):
		x = self.l.getCurrentSelection()
		return x and x[1]

	def moveToService(self,serviceref):
		if not serviceref:
			return
		index = 0
		refstr = serviceref.toString()
		for x in self.list:
			if x[1] == refstr:
				self.instance.moveSelectionTo(index)
				break
			index += 1

	def moveToEventId(self, eventId):
		if not eventId:
			return
		index = 0
		for x in self.list:
			if x[1] == eventId:
				self.instance.moveSelectionTo(index)
				break
			index += 1

	def fillSimilarList(self, refstr, event_id):
		t = time()
	 # search similar broadcastings
		if event_id is None:
			return
		l = self.epgcache.search(('RIBND', 1024, eEPGCache.SIMILAR_BROADCASTINGS_SEARCH, refstr, event_id))
		if l and len(l):
			l.sort(key=lambda x: x[2])
		self.list = l
		self.l.setList(self.list)
		self.selectionChanged()
		print time() - t
