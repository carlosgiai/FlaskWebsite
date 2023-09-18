from flask import Blueprint, render_template, request, flash, redirect, url_for

from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from .models import User, Membership
from werkzeug.security import generate_password_hash, check_password_hash
from . import db   ##means from __init__.py import db
from flask_login import login_user, login_required, logout_user, current_user
from flask import session
from website.models import Membership

import os 
import stripe

from langchain import OpenAI, ConversationChain, LLMChain, PromptTemplate
from langchain.memory.buffer_window import ConversationBufferWindowMemory
from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    HumanMessage,
)



os.environ['OPENAI_API_KEY'] = ''

template = """ Eres el chatbot del negocio "Interlight", un negocio de productos eléctricos ubicado en Montañeses 2435, CABA, Argetnina. Te llamas "InterChat". 
Ayudarás a quien sea que te hable (El cliente) con consultas sobre el negocio.

Interlight abre de Lunes a Viernes de 8:00 a 17:00 horas. Y Sábados de 8:00 a 13:00.

Los numeros de WhatsApp para pedidos o consulta de stock son +54 11 4782 6043 o también +54 11 4896 1217.

Inerlight vende productos como:

- Lamparas Led
- Disyuntores
- Térmicas
- Tapas de luz
- Caños
- Cajas y Tableros
- Cables a medida

Entre muchas otras cosas



Cliente {human_input}

Respuesta:
"""

prompt1 = PromptTemplate(input_variables=["human_input"], template=template)


auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(email=email, first_name=first_name, password=generate_password_hash(
                password1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up.html", user=current_user)

from flask import g
from flask import session

# @auth.route('/chatbot', methods=['GET', 'POST'])
# def chatbot_go():
#     if request.method == 'POST':
#         if 'chat_history' not in session:
#             session['chat_history'] = []
        
#         prompt = request.form.get('prompt')
#         chatgpt_chain = LLMChain(
#             llm=OpenAI(model_name='text-davinci-003', callbacks=[StreamingStdOutCallbackHandler()], temperature=0),
#             prompt=prompt1,
#             verbose=True,
#             memory=ConversationBufferWindowMemory(k=2)
#         )

#         answer = chatgpt_chain.predict(human_input=prompt)

#         # Initialize chat_history if it doesn't exist
        

#         # Append user's message and chatbot's response to the chat_history
#         session['chat_history'].append({'sender': 'user', 'text': prompt})
#         session['chat_history'].append({'sender': 'chatbot', 'text': answer})

#         # IMPORTANT: Save changes to the session
#         session.modified = True

#         return redirect(url_for('auth.chatbot_go'))
    
    
#     chat_history = session.get('chat_history', [])
#     return render_template("chatbot.html", user=current_user, chat_history=chat_history)

from flask import jsonify

@auth.route('/chatbot', methods=['GET', 'POST'])
def chatbot_go():
    if request.method == 'POST':
        if 'chat_history' not in session:
            session['chat_history'] = []

        prompt = request.form.get('prompt')
        chatgpt_chain = LLMChain(
            llm=OpenAI(model_name='text-davinci-003', callbacks=[StreamingStdOutCallbackHandler()], temperature=0.5),
            prompt=prompt1,
            verbose=True,
            memory=ConversationBufferWindowMemory(k=2)
        )

        answer = chatgpt_chain.predict(human_input=prompt)

        # Append user's message and chatbot's response to the chat_history
        session['chat_history'].append({'sender': 'user', 'text': prompt})
        session['chat_history'].append({'sender': 'chatbot', 'text': answer})

        # Save changes to the session
        session.modified = True

        # Return the user's message and chatbot's response as JSON for the AJAX call
        return jsonify(userMessage=prompt, chatbotMessage=answer)

    chat_history = session.get('chat_history', [])
    return render_template("chatbot.html", user=current_user, chat_history=chat_history)


@auth.route('/delete-history', methods=['POST'])
def delete_history():
    if 'chat_history' in session:
        del session['chat_history']
    return redirect(url_for('auth.chatbot_go'))







# MEMBERSHIP


# Your Stripe secret key (you'll have this in your Stripe Dashboard)
stripe_keys = {
  'secret_key': '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',
  'publishable_key': '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'
}

stripe.api_key = stripe_keys['secret_key']

@auth.route('/be-a-member', methods=['GET'])
@login_required
def be_a_member():
    print(current_user.has_membership)
    return render_template('membership.html', user=current_user)

@auth.route('/charge', methods=['POST'])
@login_required
def charge():
    if current_user.has_membership:
        flash("You already have a membership!")
        return redirect(url_for("auth.be_a_member"))
    else:


        # Amount in cents
        amount = 500

        # Retrieve additional data from form
        name = request.form['name']
        email = request.form['email']
        stripe_token = request.form['stripeToken']

        # Create a Stripe customer using the provided email and source
        customer = stripe.Customer.create(
            email=email,
            source=stripe_token
        )

        # Create a charge using the customer ID
        charge = stripe.Charge.create(
            customer=customer.id,
            amount=amount,
            currency='usd',
            description=f'Membership for {name}'
        )

        # (Optional) Save membership details in your database here
        # ...
        current_user.has_membership = True
        # Assuming you're using SQLAlchemy
        new_membership = Membership(user_id=current_user.id)
        db.session.add(new_membership)
        db.session.commit()

        flash('Thanks for your payment!', 'success')
        return redirect(url_for('auth.be_a_member'))
        # else:
        #     flash("You already have a membership!")
        #     return redirect(url_for('auth.login'))
        
