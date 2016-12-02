#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author ittnaDevs
# version 1.0, 09.03.2016 // T1 alkaa. Pahasti kesken. Tarkista tiedostopolut.
# version 1.1, 10.03.2016 // T1 jatkuu. KESKEN. Uusimmat vielä testaamatta. ja app.route puuttuu.
# version 1.2, 11.03.2016 // T1 jatkuu. KESKEN. Lisääminen kesken - jotain menee kokoajan pieleen.
# version 1.3, 16.03.2016 // T1 valmis. Homma helpottui paljon, kun flaskin sai toimimaan. Ei pitäisi unohtaa flaskin loppua KOSKAAN!
# version 1.4, 16.03.2016 // T3 alkaa.
# version 1.5, 17.03.2016 // T3 jatkuu.
# version 1.6, 18.03.2016 // T3 valmis.
# version 1.7, 18.03.2016 // T5 alkaa. TODO: Laita kirjautumiseen jotain järkevää.
# version 1.8, 21.03.2016 // T5 jatkuu. Kirjautuminen toimii vihdoinkin, kun useat pikkuvirheet sai korjattua.
# version 1.9, 21.03.2016 // T5 jatkuu. Vielä jäi hieman kesken. Kaikki muu toteutettu paitsi viimeinen pykälä.

from flask import Flask, session, redirect, url_for, escape, request, Response, render_template, make_response
import sqlite3
import logging
import os
import json
import sys
import hashlib
from functools import wraps

app = Flask(__name__)
app.debug = True
app.secret_key = 'VERYSECRETKEY'

TIETOKANTA = 'path/to/database'
poikkeukset = {'Ohje':'ReseptiID','Liittyy':'Resepti_ReseptiID'}
OMASALAINENAVAIN = "MYOWNSECRETKEY"
EMAILOSOITE = "ENCRYPTEDEMAIL"
SALAINENSALASANA = "ENCRYPTEDPASSWORD"
COOKIE2 = 'COOKIE2'

def auth(f):
    ''' Tämä decorator hoitaa kirjautumisen tarkistamisen ja ohjaa tarvittaessa kirjautumissivulle
    '''
    @wraps(f)
    def decorated(*args, **kwargs):
        # tässä voisi olla monimutkaisempiakin tarkistuksia mutta yleensä tämä riittää
        if not COOKIE2 in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def db_connect():
    """
    Yhdistetään tietokantaan.
    """
    con = ""
    try:
        con = sqlite3.connect(os.path.abspath(TIETOKANTA));
        con.row_factory = sqlite3.Row
    except Exception as e:
        con = ""
    return con

@app.route('/login', methods=['POST','GET'])
def login():
    """
    Fetches log-in page.
    """
    virhe = ""
    try:
        virhe = request.values.get('virhe',"")
    except Exception as e:
        virhe = ""

    name = u'Index'
    resp = make_response(render_template('login.xml',name=name,virhe=virhe))
    resp.charset = "UTF-8"
    resp.mimetype = "text/xml"
    return resp


@app.route('/hae_index', methods=['GET','POST'])
@auth
def index():
    """Hakee reseptilomakkeen perusrakenteen.
    """
    virhe = ""
    name = 'Index'
    resp = make_response(render_template('hae_index.xml',name=name))
    resp.charset = "UTF-8"
    resp.mimetype = "text/xml"
    return resp

@app.route('/login_tarkistus', methods=['GET','POST'])
def login_tarkistus():
    """
    Tarkistetaan onko kirjauduttu.
    """
    tunnus = ""
    salasana = ""
    virhe = ""
    l = []
    tiedot = {}
    resp = ""

    try:
        tunnus = request.values.get('tunnus',"")
    except Exception as e:
        tunnus = ""
    try:
        salasana = request.values.get('salasana',"")
    except Exception as e:
        salasana = ""

    if len(tunnus) <= 0:
        virhe = u"Tunnus oli liian lyhyt. Täytä lomake uudelleen."
        l.append(virhe)
    if len(salasana) <= 0:
        virhe = u"Salasana oli liian lyhyt. Täytä lomake uudelleen."
        l.append(virhe)
    if len(l) == 0:
        m1 = hashlib.sha512()
        m1.update(OMASALAINENAVAIN + tunnus)
        if m1.digest() == EMAILOSOITE:
            m1 = hashlib.sha512()
            m1.update(OMASALAINENAVAIN + salasana)
            if m1.digest() == SALAINENSALASANA:
                tiedot['tulokset'] = u'OK'
                tiedot['kirjautunut'] = COOKIE2
                session[COOKIE2] = COOKIE2
            else:
                virhe = u'Salasana oli väärä. Täytä lomake uudelleen.'
                l.append(virhe)
        else:
            virhe = u'Tunnus oli väärä. Täytä lomake uudelleen.'
            l.append(virhe)

        # if COOKIE2 in session:
        #     virhe = ""

    # else:
    tiedot['virhe'] = virhe
    resp = make_response(json.dumps(tiedot),200)
    resp.charset = "UTF-8"
    resp.mimetype = "application/json"
    # return resp

    return resp


@app.route('/hae_reseptit', methods=['GET','POST'])
@auth
def hae_reseptit():
    """
    Hakee tietokannasta löytyvät reseptit.
    """
    sqlReseptit = """
    SELECT ru.RuokalajiID AS Ru_ruokalajiid, ru.Nimi AS Ru_nimi, re.RuokalajiID AS RuokalajiID, re.Nimi AS Nimi, re.Kuvaus,re.Henkilomaara,re.ReseptiID
    FROM Resepti re, Ruokalaji ru
    WHERE ru.RuokalajiID = re.RuokalajiID
    ORDER BY UPPER(ru.Nimi), UPPER(re.Nimi)
    """
    con = db_connect()
    tulokset = []
    virheet = []
    cur = ""
    try:
        cur = con.cursor()
        cur = cur.execute(sqlReseptit)
    except Exception as e:
        virheet.append(u"Tapahtui virhe haettaessa reseptejä: " + str(e))

    s = ""
    for o in cur:
        if s != o['ru_nimi']:
            s = o['ru_nimi']
            tulokset.append({'ru_nimi':o['Ru_nimi'],'nimi':o['Nimi'],'kuvaus':o['Kuvaus'],'henkilomaara':o['Henkilomaara'],'reseptiid':o['ReseptiID'],'ruokalajiid':o['RuokalajiID']})
        else:
            tulokset.append({'ru_nimi':"",'nimi':o['Nimi'],'kuvaus':o['Kuvaus'],'henkilomaara':o['Henkilomaara'],'reseptiid':o['ReseptiID'],'ruokalajiid':o['RuokalajiID']})
    con.close()
    name = 'Reseptitlista'
    resp = make_response(render_template('hae_reseptit.xml',tulokset=tulokset,virheet=virheet,name=name))
    resp.charset = "UTF-8"
    resp.mimetype = "text/xml"
    return resp

@app.route('/hae_ruokalajit',methods=['GET'])
@auth
def hae_ruokalajit():
    """
    Hakee ruokalajit.
    """
    sqlRuokalajit = """
    SELECT *
    FROM Ruokalaji
    ORDER BY UPPER(Nimi)
    """
    con = db_connect();
    cur = ""
    virheet = []
    tulokset = []
    try:
        cur = con.cursor()
        cur = cur.execute(sqlRuokalajit)
    except Exception as e:
        virheet.append(u"Tapahtui virhe haettaessa ruokalajeja: " + str(e))

    for o in cur:
        tulokset.append({'nimi':o['Nimi'],'kuvaus':o['Kuvaus'],'ruokalajiid':o['RuokalajiID']})

    con.close()
    name = 'Ruokalajitlista'
    resp = make_response(render_template('hae_ruokalajit.xml',tulokset=tulokset,virheet=virheet,name=name))
    resp.charset = "UTF-8"
    resp.mimetype = "text/xml"
    return resp

@app.route('/poista_resepti', methods=['GET','POST'])
@auth
def poista_resepti():
    con = ""
    virhe = ""
    tiedot = {}
    reseptiid = 0
    con = db_connect()
    sqlPoistaResepti = """
    DELETE FROM resepti
    WHERE ReseptiID = :reseptiid
    """
    if request.method == 'POST':
        try:
            reseptiid = int(request.values.get('dataid',0))
        except:
            reseptiid = 0
        if reseptiid >= 1:
            cur = ""
            try:
                cur = con.cursor()
                cur.execute(sqlPoistaResepti,{'reseptiid':reseptiid})
                con.commit()
            except Exception as e:
                virhe = u"Tapahtui virhe yritettäessä poistaa reseptiä. Virhe: "+ str(e)
                con.rollback()
    con.close()
    tiedot['virhe'] = virhe
    resp = make_response(json.dumps(tiedot),200)
    resp.charset = "UTF-8"
    resp.mimetype = "application/json"
    return resp

@app.route('/', methods=['GET','POST'])
@auth
def lisaa_resepti():
    virhe = ""
    tiedot = {}
    reseptin_nimi = ""
    reseptin_kuvaus = '-'
    reseptin_henkilomaara = 0
    ruokalajiid = 0
    con = ""
    con = db_connect()
    if request.method == 'POST':
        ALIOHJELMA = request.values.get('aliohjelma')
        if ALIOHJELMA == u"RESEPTI":
            """
            Lisää käyttäjän syöttämän reseptin tiedot tietokantaan.
            """
            sqlLisaaresepti = """
            INSERT INTO Resepti (Nimi, Kuvaus, Henkilomaara, RuokalajiID)
            VALUES (:nimi, :kuvaus, :henkilomaara, :ruokalaji)
            """
            try:
                reseptin_nimi = request.values.get('r_nimi',"")
                #reseptin_nimi = string.capwords(reseptin_nimi) # ei pelaa tällä kertaa!!!
            except Exception as e:
                reseptin_nimi = ""
            try:
                reseptin_kuvaus = request.values.get('r_kuvaus',"")
            except Exception as e:
                reseptin_kuvaus = '-'
            try:
                reseptin_henkilomaara = int(request.values.get('r_henkilomaara',0))
            except Exception as e:
                reseptin_henkilomaara = 0
            try:
                ruokalajiid = int(request.values.get('valittu', 0))
            except:
                ruokalajiid = 0

            if len(reseptin_nimi) and reseptin_henkilomaara >= 1 and ruokalajiid >= 1:

                cur = ""
                try:
                    cur = con.cursor()
                    cur.execute(sqlLisaaresepti,{'nimi':reseptin_nimi,'kuvaus':reseptin_kuvaus,'henkilomaara':reseptin_henkilomaara, 'ruokalaji':ruokalajiid})
                    con.commit()
                    #virhe = "Paasi commitoimaan"
                except Exception as e:
                    virhe = u"Tapahtui virhe lisättäessä reseptiä tietokantaan: " + str(e)
                    con.rollback()
            elif len(reseptin_nimi) == 0:
                virhe = u"Resepti tarvitsee nimen."
            elif reseptin_henkilomaara <= 0:
                virhe = u"Henkilömäärä oli liian pieni."
            elif ruokalajiid <= 0:
                virhe = u'Ruokalajin valinnassa on tapahtunut virhe.'

        elif ALIOHJELMA == u"MUOKKAA":
            """MIkäli painettu linkkiä, haetaankin reseptin tiedot ja palautetaan ne json muodossa.
            """
            sqlResepti="""
            SELECT * FROM Resepti WHERE ReseptiID = :reseptiid
            """
            try:
                resepti_id = int(request.values.get('r_id',0))
            except:
                resepti_id = 0
            try:
                cur = con.cursor()
                if resepti_id >= 1:
                    cur = cur.execute(sqlResepti,{'reseptiid':resepti_id})
            except Exception as e:
                virhe = u"Tapahtui virhe haettaessa reseptin tietoja tietokannasta: "+str(e)

            tulokset = []
            for o in cur:
                tulokset.append({'nimi':o['Nimi'],'kuvaus':o['Kuvaus'],'henkilomaara':o['Henkilomaara'],'reseptiid':o['ReseptiID'],'ruokalajiid':o['RuokalajiID']})
            tiedot['tulokset'] = tulokset

        elif ALIOHJELMA == u'PAIVITA':
            """
            Päivitetään muokattavan reseptin tiedot.
            """
            sqlPaivita = """
            UPDATE resepti
            SET Nimi = :nimi, Kuvaus = :kuvaus, Henkilomaara = :henkilomaara, RuokalajiID = :valittu
            WHERE ReseptiID = :reseptiid
            """
            nimi = ""
            kuvaus = ""
            henkilomaara = 0
            valittu = 0
            reseptiid = 0
            try:
                nimi = request.values.get('nimi',"")
            except Exception as e:
                nimi = ""
            try:
                kuvaus = request.values.get('kuvaus',"")
            except Exception as e:
                kuvaus = "-"
            try:
                henkilomaara = int(request.values.get('henkilomaara',0))
            except Exception as e:
                henkilomaara = 0
            try:
                valittu = int(request.values.get('valittu',0))
            except Exception as e:
                valittu = 0
            try:
                reseptiid = int(request.values.get('reseptiid', 0))
            except Exception as e:
                reseptiid = 0

            l = []
            if valittu < 1:
                virhe = u'Ruokalajin valinta oli huono.'
                l.append(virhe)
            if len(nimi) <= 0:
                virhe = u'Resepti tarvitsee nimen.'
                l.append(virhe)
            if henkilomaara < 1:
                virhe = u'Henkilömäärä oli liian pieni'
                l.append(virhe)
            if reseptiid <= 0:
                virhe = u'Reseptin id:tä ei löytynyt.'
                l.append(virhe)

            cur = ""
            if len(l) == 0:
                try:
                    cur = con.cursor()
                    cur.execute(sqlPaivita,{'nimi':nimi,'kuvaus':kuvaus,'henkilomaara':henkilomaara,'valittu':valittu,'reseptiid':reseptiid})
                    con.commit()
                    virhe = ""
                except Exception as e:
                    con.rollback()
                    virhe = u'Päivityksessä tapahtui virhe: '+ str(e)

    con.close()
    tiedot['virhe'] = virhe
    resp = make_response(json.dumps(tiedot),200)
    resp.charset = "UTF-8"
    resp.mimetype = "application/json"
    return resp




#########
if __name__ == '__main__':
    app.debug = True
    app.run(debug=True)
