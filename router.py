#!/usr/bin/python

from socket import *
import sys, logging, os
import struct
#import math

TOTAL_ROUTERS = 5

class pktHELLO:
	def __init__(self, routerId, linkId):
		self.routerId = routerId
		self.linkId = linkId

	def convertToByteArray(self):
		return struct.pack("<II", self.routerId, self.linkId)

	def generateLogMessageHello(self, isSend, routerId):
		if isSend:
			return "R" + str(routerId) + " sends a HELLO: routerId " + str(self.routerId) + " linkId " + str(self.linkId)
		else:
			return "R" + str(routerId) + " receives a HELLO: routerId " + str(self.routerId) + " linkId " + str(self.linkId)

class pktLSPDU:
	def __init__(self, sender, routerId, linkId, cost, via):
		self.sender = sender
		self.routerId = routerId
		self.linkId = linkId
		self.cost = cost
		self.via = via

	def convertToByteArray(self):
		return struct.pack("<IIIII", self.sender, self.routerId, self.linkId, self.cost, self.via)

	def generateLogMessageLSPDU(self, isSend, routerId):
		if isSend:
			return "R" + str(routerId) + " sends a LSPDU: sender " + str(self.sender) + " routerId " + str(self.routerId) + " linkId " + str(self.linkId) + " cost " + str(self.cost) + " via " + str(self.via)
		else:
			return "R" + str(routerId) + " receives a LSPDU: sender " + str(self.sender) + " routerId " + str(self.routerId) + " linkId " + str(self.linkId) + " cost " + str(self.cost) + " via " + str(self.via)

class pktINIT:
	def __init__(self, routerId):
		self.routerId = routerId

	def convertToByteArray(self):
		return struct.pack("<I", self.routerId)

	def generateLogMessageInit(self, routerId):
		return "R" + str(routerId) + " sends an INIT: routerId " + str(self.routerId)

class linkCost:
	def __init__(self, linkId, cost):
		self.linkId = linkId
		self.cost = cost

class circuitDB:
	def __init__(self, nbrLink, linkCost):
		self.nbrLink = nbrLink
		self.linkCost = linkCost

	def generateLogMessageCircuitDB(self, routerId):
		logMessage = "\n" + "R" + str(routerId) + " receives a CIRCUIT_DB: nbrLink " + str(self.nbrLink) + "\n"
		for lc in self.linkCost:
			logMessage = logMessage + "linkId: " + str(lc.linkId) + " AND cost: " + str(lc.cost) + "\n"
		return logMessage

class RoutingInformationBase:
	def __init__(self, routerId):
		self.routerId = routerId
		self.pathCost = dict()

	def addPathCost(self, dest, path, cost):
		if not(dest in self.pathCost.keys()):
			self.pathCost[dest] = (path, cost)
		else:
			if cost < self.pathCost[dest][1]:
				self.pathCost[dest] = (path, cost)

	def shortestPathFirst(self, u, linkStateDatabase):
		# initialization
		predeccesors = dict()
		predeccesors[u] = None
		N = list()
		N.append(u)

		neighbours = linkStateDatabase.getNeighbour(u)

		# initialize/update RIB
		for v in range(1, TOTAL_ROUTERS + 1):
			if v != u and v in neighbours:
				self.addPathCost(v, v, linkStateDatabase.getCost(u, v))
				predeccesors[v] = v
			elif v == u:
				self.addPathCost(v, "Local", 0)
			else:
				self.addPathCost(v, None, float("inf"))
				predeccesors[v] = None

		while len(N) < TOTAL_ROUTERS:
			# find minimum cost pair
			minCost = (None, float("inf"))
			for w in range(1, TOTAL_ROUTERS + 1):
				if not(w in N) and self.pathCost[w][1] < minCost[1]:
					minCost = (w, self.pathCost[w][1])
			N.append(minCost[0])
			# iterate to expand the frontier of minimum cost
			for v in linkStateDatabase.getNeighbour(minCost[0]):
				if not(v in N):
					newCost = min(self.pathCost[v][1], self.pathCost[minCost[0]][1] + linkStateDatabase.getCost(minCost[0], v))
					predeccesors[v] = predeccesors[minCost[0]]
					newPath = predeccesors[v]
					#newPath = None
					#if newCost == self.pathCost[v][1]:
					#	newPath = predeccesors[v]
					#else:
					#	predeccesors[v] = predeccesors[minCost[0]]
					#	newPath = predeccesors[v]
					self.addPathCost(v, newPath, newCost)

	def generateLogMessageRIB(self):
		logMessage = "\n" + "# RIB:" + "\n"
		for key, value in self.pathCost.items():
			if str(value[0]) == "Local":
				logMessage = logMessage + "R" + str(self.routerId) + " -> " + "R" + str(key) + " -> " + str(value[0]) + ", " + str(value[1]) + "\n"
			elif value[1] == float("inf"):
				logMessage = logMessage + "R" + str(self.routerId) + " -> " + "R" + str(key) + " -> " + "INF, INF" + "\n"
			else:
				logMessage = logMessage + "R" + str(self.routerId) + " -> " + "R" + str(key) + " -> " + "R" + str(value[0]) + ", " + str(value[1]) + "\n"
		return logMessage

class LinkStateDataEntry:
	def __init__(self, link, cost, dest):
		self.nbrLink = 1
		self.linkStateList = list()
		self.linkStateList.append((link, cost, dest))

	def addEntry(self, link, cost, dest):
		updated = False
		for i in range(len(self.linkStateList)):
			if (self.linkStateList[i][0] == link and self.linkStateList[i][1] == cost and self.linkStateList[i][2] != dest):
				self.linkStateList[i] = (link, cost, dest)
				updated = True
				return updated
		if not((link, cost, dest) in self.linkStateList):
			self.linkStateList.append((link, cost, dest))
			self.nbrLink = self.nbrLink + 1
			updated = True
		return updated

class LinkStateDatabase:
	def __init__(self, routerId):
		self.routerId = routerId
		self.linkStateData = dict()

	def updateLinkStateData(self, routerId, link):
		updated = False
		cost = None
		for lsdEntry in self.linkStateData[self.routerId].linkStateList:
			if lsdEntry[0] == link:
				cost = lsdEntry[1]
		self.linkStateData[self.routerId].addEntry(link, cost, routerId)
		return updated

	def addLinkStateData(self, routerId, link, cost):
		updated = False
		dest = None
		for router in self.linkStateData.keys():
			if router != routerId:
				for lsdEntry in self.linkStateData[router].linkStateList:
					if lsdEntry[0] == link:
						dest = router
		#print(dest)
		if not(routerId in self.linkStateData.keys()):
			self.linkStateData[routerId] = LinkStateDataEntry(link, cost, dest)
			updated = True
		else:
			updated = self.linkStateData[routerId].addEntry(link, cost, dest)
		if updated and not(dest == None):
			placeHolderBoolean = self.linkStateData[dest].addEntry(link, cost, routerId)
		return updated

	def getNeighbour(self, routerId):
		neighboursFound = list()
		if routerId in self.linkStateData.keys():
			for lsdEntry in self.linkStateData[routerId].linkStateList:
				if lsdEntry[2] != None and lsdEntry[2] in self.linkStateData.keys():
					neighboursFound.append(lsdEntry[2])
		return neighboursFound

	def getCost(self, router1, router2):
		cost = float("inf")
		#if router1 == router2:
		#	return 0
		if router1 in self.linkStateData.keys():
			for lsdEntry in self.linkStateData[router1].linkStateList:
				if lsdEntry[2] == router2 and lsdEntry[2] in self.linkStateData.keys():
					cost = lsdEntry[1]
		return cost

	def getLink(self, routerId, neighbour):
		link = None
		#print(routerId)
		#print(neighbour)
		#print(self.linkStateData.keys())
		if routerId in self.linkStateData.keys():
			for lsdEntry in self.linkStateData[routerId].linkStateList:
				if lsdEntry[2] == neighbour:
					link = lsdEntry[0]
					#print(link)
		return link

	def generateLogMessageLSD(self):
		logMessage = "\n" + "# Topology Database:" + "\n"
		for key, value in self.linkStateData.items():
			logMessage = logMessage + "R" + str(self.routerId) + " -> " + "R" + str(key) + " nbr link " + str(value.nbrLink) + "\n"
			for lsdEntry in value.linkStateList:
				logMessage = logMessage + "R" + str(self.routerId) + " -> " + "R" + str(key) + " link " + str(lsdEntry[0]) + " cost " + str(lsdEntry[1]) + " dest " + str(lsdEntry[2]) + "\n"
		return logMessage

def main():
	# parameter check
	if len(sys.argv) == 5:
		routerId = int(sys.argv[1])
		nseHost = sys.argv[2]
		nsePort = int(sys.argv[3])
		routerPort = int(sys.argv[4])
	else:
		print "Error: Incorrect number of command line arguments."
		sys.exit(1)
	# initialize log and add file handler to generate log file
	logName = "router" + str(routerId) + ".log"
	if (os.path.isfile(logName)): 
		os.remove(logName)
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.DEBUG)
	fh = logging.FileHandler(logName)
	fh.setLevel(logging.DEBUG)
	logger.addHandler(fh)

	routerSocket = socket(AF_INET, SOCK_DGRAM)
	routerSocket.bind(('', routerPort))

	# initialize link state database and routing info base
	linkStateDatabase = LinkStateDatabase(routerId)
	routingInfoBase = RoutingInformationBase(routerId)

	# sends an INIT packet (struct pkt_INIT) to the network
	initPacket = pktINIT(routerId)
	byteArrayForInitPacket = initPacket.convertToByteArray()
	routerSocket.sendto(initPacket.convertToByteArray(), (nseHost, nsePort))
	logger.info(initPacket.generateLogMessageInit(routerId))

	# receives a packet back from the nse that contain the circuit database
	byteData, clientAddr = routerSocket.recvfrom(4096)
	nbrLink = struct.unpack_from("<I", byteData, 0)[0]
	linkCostList = list()
	for i in range(nbrLink):
		byteIndex = 4 + (i * 8)
		linkCostData = struct.unpack_from("<II", byteData, byteIndex)
		linkCostList.append(linkCost(linkCostData[0], linkCostData[1]))
	circuitDatabase = circuitDB(nbrLink, linkCostList)
	logger.info(circuitDatabase.generateLogMessageCircuitDB(routerId))

	# puts data into the Link State Database and sends HELLO_PDU to all the links discovered
	for neighbour in circuitDatabase.linkCost:
		updated = linkStateDatabase.addLinkStateData(routerId, neighbour.linkId, neighbour.cost)
		# log LSD
		if updated:
			logger.info(linkStateDatabase.generateLogMessageLSD())
		helloPacket = pktHELLO(routerId, neighbour.linkId)
		byteArrayForHelloPacket = helloPacket.convertToByteArray()
		routerSocket.sendto(byteArrayForHelloPacket, (nseHost, nsePort))
		logger.info(helloPacket.generateLogMessageHello(True, routerId))

	neighbourFound = list()

	while(True):
		#print("WAIT")
		byteDataFound, clientAddr = routerSocket.recvfrom(4096)
		#print("GO")
		byteLength = len(byteDataFound)
		#print(byteLength)
		# hello packet received
		if (byteLength == 8):
			helloPacketRecv = struct.unpack_from("<II", byteDataFound)
			helloPacket = pktHELLO(helloPacketRecv[0], helloPacketRecv[1])
			logger.info(helloPacket.generateLogMessageHello(False, routerId))
			# log lsd
			updated = linkStateDatabase.updateLinkStateData(helloPacket.routerId, helloPacket.linkId)
			if updated:
				logger.info(linkStateDatabase.generateLogMessageLSD())
			for neighbour in circuitDatabase.linkCost:
				packetLSPDU = pktLSPDU(routerId, routerId, neighbour.linkId, neighbour.cost, helloPacket.linkId)
				byteArrayForLSPDUPacket = packetLSPDU.convertToByteArray()
				routerSocket.sendto(byteArrayForLSPDUPacket, (nseHost, nsePort))
				logger.info(packetLSPDU.generateLogMessageLSPDU(True, routerId))
			# indicates that this neighbouring router is now 'discovered'
			neighbourFound.append(helloPacket.routerId)
		# lspdu packet received
		elif (byteLength == 20):
			lspduPacketRecv = struct.unpack_from("<IIIII", byteDataFound)
			lspduPacket = pktLSPDU(lspduPacketRecv[0], lspduPacketRecv[1], lspduPacketRecv[2], lspduPacketRecv[3], lspduPacketRecv[4])
			logger.info(lspduPacket.generateLogMessageLSPDU(False, routerId))
			updated = linkStateDatabase.addLinkStateData(lspduPacket.routerId, lspduPacket.linkId, lspduPacket.cost)
			# log lsd
			if updated:
				logger.info(linkStateDatabase.generateLogMessageLSD())
				for neighbour in neighbourFound:
					if neighbour != lspduPacket.sender:
						#print(routerId)
						#print(lspduPacket.routerId)
						#print(lspduPacket.linkId)
						#print(lspduPacket.cost)
						#print(routerId)
						#print(neighbour)
						#print(linkStateDatabase.getLink(routerId, neighbour))
						packetLSPDU = pktLSPDU(routerId, lspduPacket.routerId, lspduPacket.linkId, lspduPacket.cost, linkStateDatabase.getLink(routerId, neighbour))
						byteArrayForLSPDUPacket = packetLSPDU.convertToByteArray()
						routerSocket.sendto(byteArrayForLSPDUPacket, (nseHost, nsePort))
						logger.info(packetLSPDU.generateLogMessageLSPDU(True, routerId))
				# run shortest path first algorithm
				routingInfoBase.shortestPathFirst(routerId, linkStateDatabase)
				logger.info(routingInfoBase.generateLogMessageRIB())
		else:
			print "Error: Incorrect packet length."
			sys.exit(1)

main()