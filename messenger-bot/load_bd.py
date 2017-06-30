#!/usr/bin/env python
# -*- coding: utf-8 -*-
import MySQLdb, codecs

#variable = unicode(string,'UTF-8')
#for row in cursor.fetchall():
unicode(['utf-8'])
db = MySQLdb.connect(user='root', host='localhost', db='movimien_socialideation_aux')
cursor = db.cursor()

def more_votes():
	"" "Collect data (positive_votes,title,url)from the app_idea table of the database" ""
	query = "select positive_votes,title,url from app_idea order by positive_votes desc;"
	cursor.execute(query)
	lista = []
	dic1t={}
	for i,j,k in cursor.fetchall():
		dict1=[int(i),{j:k}]
		lista.extend(dict1)
	list_more_votes=[]
	for x in lista[0:6]:
	  list_more_votes.append(x)
	return list_more_votes

def load_low_ideas():
	"" "Order the campaign and Collect data (title, campaign_id)from the app_idea table of the database" ""
	query ="select campaign_id, count(*) from (select distinct title, campaign_id from app_idea) as temp group by campaign_id;"
	cursor.execute(query)
	dic1={}
	lista = []
	list_less_ideas=[]
	for i,j in cursor.fetchall():
		if i==7:
			dict1=[int(j),{'http://vozyvoto.ideascale.com/a/ideas/recent/campaign-filter/byids/campaigns/51599':'Inspiracion'}]
		elif i==8:
			dict1=[int(j),{'http://vozyvoto.ideascale.com/a/ideas/recent/campaign-filter/byids/campaigns/51594':'Gestion Municipal'}]
		elif i==9:
			dict1=[int(j),{'http://vozyvoto.ideascale.com/a/ideas/recent/campaign-filter/byids/campaigns/51595':'Movilidad Urbana Sostenible'}]
		elif i==10:
			dict1=[int(j),{'http://vozyvoto.ideascale.com/a/ideas/recent/campaign-filter/byids/campaigns/51596':'Basura Cero!'}]
		elif i==11:
			dict1=[int(j),{'http://vozyvoto.ideascale.com/a/ideas/recent/campaign-filter/byids/campaigns/51597':'Mercados Municipales'}]
		elif i==12:
			dict1=[int(j),{'http://vozyvoto.ideascale.com/a/ideas/recent/campaign-filter/byids/campaigns/51692':'Resilencia Urbana'}]
		elif i==13:
			dict1=[int(j),{'http://vozyvoto.ideascale.com/a/ideas/recent/campaign-filter/byids/campaigns/51693':'Infraestructura'}]
		lista.extend(dict1)
	for x in lista[0:6]:
		list_less_ideas.append(x)
	return list_less_ideas

def load_low_reply():
	"" "Collect data (comments, title, url)from the app_idea table of the database" ""
	query ="select comments, title, url from app_idea order by comments;"
	cursor.execute(query)
	list_less_reply=[]
	lista = []
	dict1={}
	for i,j,k in cursor.fetchall():
		if len(j)!=0:
			dict1=[int(i),{j:k}]
			lista.extend(dict1)
	#print lista
	for x in lista[0:6]:
		list_less_reply.append(x)
	return list_less_reply


if __name__=='__main__':
	list_more_votes=more_votes()
	list_less_ideas=load_low_ideas()
	list_less_reply=load_low_reply()

