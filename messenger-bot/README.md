Bot Social (Voz y Voto)
===============
Social bot (Voz y Voto) is an assistant of the application of [social-ideation] that is connected to [Voz y Voto](http://vozyvoto.ideascale.com/) and at the same time to the group of the Facebook [Grupo Voz y Voto](https://www.Facebook.com/groups/1655519178027107/) looking solutions with ideas for the city of Asunción.

Getting started
-------------
1. [Create a Facebook App](https://developers.facebook.com/apps)
2. Go to Messenger Setting 
3. [Create a new Facebook Page](https://www.facebook.com/pages/create/)
4. Execute `source env/bin/activate`
5. Create a project folder
6. Go inside the project folder and execute `pip install flask requests pymessenger`
7. Create app.py
8. Write code for webhook verification
9. Run flask app using [ngrok](https://ngrok.com) 
10. Go again to Messenger Setting and click into Setup Webhooks. Paste the url of ngrok with the port avaible in Callback URL and write "hello" in Verify Token. Select all option then "Verify and Save". Select a page to subsribe your webhook to the page events and Subscribe.
11. Go Again to Messenger Setting copy the Page Access Token and paste in to "PAGE_ACCESS_TOKEN" variable of app.py
12. In the final line of app.py write the port enabled 
13. Run app.py