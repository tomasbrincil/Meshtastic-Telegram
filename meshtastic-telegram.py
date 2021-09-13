import telebot
import re
import meshtastic
import time
import json
import sys
import io
import pickle
from pubsub import pub
import datetime
from pprint import pprint

debug = False
api_key = "1989348436:ABEvMN-CO4-X0cbEHoKKLYDq-xQj23cFcZY"

chatids_db_file = 'chati_ds.data'
fd = open(chatids_db_file, 'rb')
chatids = pickle.load(fd)

if debug:
	print("chatids loaded")
	print(chatids)

bot = telebot.TeleBot(api_key)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, "I am Meshtastic Telegram bot!\n/send messages will transmit your message\n/enable starts recieving messages to chat\n/disable will stop receiving messages\n/printurl to get url for Android APP\n/nodes print some information from NodeDB")
	if debug:
		print("Printing satbot information.")

@bot.message_handler(commands=['enable'])
def send_enable(message):
	bot.reply_to(message, "All decoded messages will be sent to this chat.")
	chatids.append(message.chat.id)
	fw = open(chatids_db_file, 'wb')
	pickle.dump(chatids, fw)
	fw.close()
	if debug:
		print("Enabling chat_id.")
		print(chatids)

@bot.message_handler(commands=['disable'])
def send_enable(message):
	bot.reply_to(message, "Receiving messages has been disabled.")
	chatids.remove(message.chat.id)
	fw = open(chatids_db_file, 'wb')
	pickle.dump(chatids, fw)
	fw.close()
	if debug:
		print("Disabling chat_id.")
		print(chatids)

@bot.message_handler(commands=['nodes'])
def send_nodes(message):
	nodes = "Last information from NodeDB:\n"
	for node in interface.nodes.values():
		user =  str(node.get('user').get('longName'))
		snr = str(node.get('snr'))
		#bl = str(node.get('batteryLevel'))
		#print(bl)
		nodes = nodes  + user + " " + snr + " dB SNR\n"
	bot.reply_to(message, nodes)
	if debug:
		print (interface.nodes.values())
		print(nodes)

@bot.message_handler(commands=['send'])
def send_message(message):
	pattern = r'/send'
	msg = message.from_user.first_name + ":" + re.sub(pattern, '', message.text)
	bot.reply_to(message, msg)
	interface.sendText(msg, hopLimit=1)
	if debug:
		print("Sending message: ")
		print(msg)

@bot.message_handler(commands=['printurl'])
def print_message(message):
	msg = interface.localNode.getURL(includeAll=False)
	bot.reply_to(message, msg)
	if debug:
		print(msg)

def onConnect(interface, topic=pub.AUTO_TOPIC):
	if debug:
		print("Connected to the interface.")

def onLost(interface, packet):
	if debug:
		print("Connection to the interface has been lost")

def onUpdated(interface, node):
	if debug:
		print("Node has been updated.")

def onReceive(interface, packet):
	try:
		packet_decoded = packet.get('decoded')
		msg = packet_decoded.get('text')
		if msg:
			message =  str(packet.get('fromId')) + ": " + msg + " [snr: " + str(packet.get('rxSnr')) + ", RSSI: " + str(packet.get('rxRssi')) + ", hoplimit: " + str(packet.get('hopLimit')) + "]"
			if debug:
				print("packet decoded")
				print(f"message: {message}")

			is_ping = msg.startswith("/ping")

			if is_ping:
				pong = "pong"  + " [snr: " + str(packet.get('rxSnr')) + ", RSSI: " + str(packet.get('rxRssi')) + ", hoplimit: " + str(packet.get('hopLimit')) + "]"
				interface.sendText(pong, hopLimit=1)
				if debug:
					print("ping received, sending pong with telemetry")
					print(pong)

			for i in chatids:
				bot.send_message(i, message)
				if debug:
					print("sending for chat_id")
					print(str(i))
					print(message)

	except Exception as ex:
		print (ex)
		pass

pub.subscribe(onReceive, "meshtastic.receive")
pub.subscribe(onConnect, "meshtastic.connection.established")
pub.subscribe(onLost, "meshtastic.connection.lost")
pub.subscribe(onUpdated, "meshtastic.node.updated")

interface = meshtastic.SerialInterface()

bot.polling()
