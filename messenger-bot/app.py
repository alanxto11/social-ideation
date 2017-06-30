#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, requests, json, operator
from flask import Flask, request
from pymessenger import Bot
from load_bd import more_votes, load_low_ideas,load_low_reply

app = Flask(__name__)


#PAGE ACCESS TOKEN
PAGE_ACCESS_TOKEN = "EAAYFD9gLOZCwBAB1k5PB0QfwhmdzvmtRDjBkD9MYBCEFcy4fVDBmSoj6KmrYjzJosyR7RtgdV8kVUDp9XZBYKhWMzLrsfFP2EBr2EKdzPvILSY4iiCLTanj9LTJzpmqizCWE8K9lI90BpP8U3aagnNN4pQqvMuUYB3AC1YLAZDZD"


bot = Bot(PAGE_ACCESS_TOKEN)

@app.route('/', methods=['GET'])
def verify():
	"" "Webhook verification" ""

	if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
		if not request.args.get("hub.verify_token") == "hello":
			return "Verification token mismatch", 403
		return request.args["hub.challenge"], 200
	return "Hello world", 200



@app.route('/', methods=['POST'])


def webhook():
	"" "Collect data from chat (facebook messenger)" ""
	data = request.get_json()
	log(data)
	if data['object'] == 'page':
		for entry in data['entry']:
			for messaging_event in entry['messaging']:
				# IDs
				sender_id = messaging_event['sender']['id']
				recipient_id = messaging_event['recipient']['id']
				#POSTBACK
				if messaging_event.get('postback'):
					messaging_text = messaging_event['postback']['payload']
					if 'payload' in messaging_event['postback']:
						if messaging_text== 'GET_STARTED_PAYLOAD':
							fun_welcome(sender_id,1)
						elif messaging_text== 'back':
							fun_welcome(sender_id,2)
						elif messaging_text== 'payload_1':
							list_topic(sender_id)
						elif messaging_text== 'payload_2':
							low_ideas(sender_id)
						elif messaging_text== 'payload_3':
							low_reply(sender_id)
				#MESSAGE
				elif messaging_event.get('message'):
					# Extracting text message
					messaging_text = messaging_event['message']['text']
					if 'text' in messaging_event['message']:
						print messaging_event
						print '\n'
						if messaging_text== 'Start' or messaging_text== 'start':
							fun_welcome(sender_id,1)
					else:
						messaging_text = 'no text'
					# Echo
					#response = messaging_text
					#bot.send_text_message(sender_id, response)

	return "ok", 200

def fun_welcome(sender_id,op):
	"" "Receive sender_id of the user type:unicode and op(typ:int) Is the value that differentiates the Welcome string . Send 3 parameters: sender_id(type:unicode), string (type:str) y buttons (type:list) to the function Send_button_message of Pymessenger Showing the main menu" ""  
	if(op==1):
		welcome_string ='Hello!\nHow is it going?\nI\'m a bot of Voice and Vote a new assistant integrated to app of Social Ideation that aims to collectively look for solutions for the city of Asunción.\nSelect the option you want to see in the following buttons:\n\n- List the ideas with more votes\n- List the campaigns with less ideas\n- List the ideas with less responses\n'	
	elif (op==2):
		welcome_string = 'Select the option you want to see in the following buttons:\n\n- List the ideas with more votes\n- List the campaigns with less ideas\n- List the ideas with less responses\n'
	buttons=[
			{'type':'postback',
			'title':'Ideas with more votes',
			'payload':'payload_1'},
			{'type':'postback',
			'title':'Campaigns with less ideas',
			'payload':'payload_2'},
			{'type':'postback',
			'title':'Ideas with less responses',
			'payload':'payload_3'}]
	bot.send_button_message(sender_id,welcome_string,buttons)


def list_topic(sender_id):
	"" "Receive sender_id of the user type:unicode. Send 3 parameters: sender_id(type:unicode), string (type:str) y buttons (type:list) to the function Send_button_message of Pymessenger Showing the 3 most voted ideas" ""  
	list_more_votes=more_votes()
	buttons = []
	b={}
	string="List the 3 most voted ideas. If you want to see. Click on the especifics buttons.\n"
	aux_counter=0
	#print list_more_votes
	for a in list_more_votes:
		if aux_counter==0:
			aux_counter=1
			count_ideas=str(a)
		else:
			aux_counter=0
			for j in a:
				titles= str(j)
				urls=(a[j])
				string=string+'- '+titles + ' has ' + count_ideas + ' votes.\n'				
				b={'type':'web_url','url': urls,'title': titles}
				buttons.append(b)
	bot.send_button_message(sender_id,string,buttons)


def low_ideas(sender_id):
	"" "Receive sender_id of the user type:unicode. Send 3 parameters: sender_id(type:unicode), string (type:str) y buttons (type:list) to the function Send_button_message of Pymessenger Showing the 3 campaigns with less ideas" ""  
	list_less_ideas=load_low_ideas()
	buttons = []
	b={}
	string="List the 3 campaigns with less ideas. If you want to see. Click on the especifics buttons.\n"
	aux_counter=0
	for a in list_less_ideas:
		if aux_counter==0:
			aux_counter=1
			count_ideas=str(a)
		else:
			aux_counter=0
			for j in a:
				urls= str(j)
				titles=str(a[j])
				if count_ideas=='0':
					string=string + '- ' + titles + ' has no ideas\n'
				else:
					string=string + '- ' + titles + ' has ' + count_ideas + ' ideas\n'
				b={'type':'web_url','url': urls,'title': titles}
				buttons.append(b)
	bot.send_button_message(sender_id,string,buttons)

def low_reply(sender_id):
	"" "Receive sender_id of the user type:unicode. Send 3 parameters: sender_id(type:unicode), string (type:str) y buttons (type:list) to the function Send_button_message of Pymessenger Showing the 5 ideas with less responses" ""  
	
	#={10:{"primero":"http://vozyvoto.ideascale.com/a/idea-v2/787144"},1:{"segundo":"http://vozyvoto.ideascale.com/a/idea-v2/789050"},3:{"tercero":"http://vozyvoto.ideascale.com/a/idea-v2/776111"}}
	list_less_reply=load_low_reply()
	buttons = []
	b={}
	string="List 5 ideas with less responses. If you want to see. Click on the especifics buttons.\n"
	aux_counter=0
	for a in list_less_reply:
		if aux_counter==0:
			aux_counter=1
			count_ideas=str(a)
		else:
			aux_counter=0
			for j in a:
				titles= str(j)
				urls=str(a[j])
				if count_ideas=='0':
					string=string + '- ' + titles + ' has no comments\n'
				else:
					string=string + '- ' + titles + ' has ' + count_ideas + ' comments\n'
				b={'type':'web_url','url': urls,'title': titles}
				buttons.append(b)
	bot.send_button_message(sender_id,string,buttons)

def log(message):
	""" Print message. Receive the parameter message"""
	#print(message)
	sys.stdout.flush()


if __name__ == "__main__":
	app.run(debug = True, port = 1024) #puerto 1024 localhost
