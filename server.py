#!/usr/bin/env python2.7
import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
from flask_table import Table, Col, create_table

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

DATABASEURI = "postgresql://ch3212:3990@104.196.18.7/w4111"
engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  try:
    g.conn.close()
  except Exception as e:
    pass

CONTEXT = {}
CONTEXT2 = {}
CONTEXT3 = {}
@app.route('/')
def index():
  return render_template("index.html")


# page1 -- players

@app.route('/page1')
def page1():
  return render_template("player.html", **CONTEXT)

@app.route('/player', methods = ["POST"])
def add():
  name = request.form['name']
  cursor = g.conn.execute(
    "SELECT p.full_name AS player_name, th.name AS team_name, s.year, pf.pg_min AS avg_min,"
    " pf.pg_point AS avg_point, pf.pg_rebound AS avg_rebound, pf.pg_assist AS avg_assist, pf.pg_block AS avg_block"
    " FROM players p, play_for pf, teams_home th, seasons s"
    " WHERE p.player_id = pf.player_id AND pf.team_id = th.team_id AND pf.season_id = s.season_id AND"
    " (p.full_name = '%s' OR p.name = '%s') ORDER BY s.year DESC" % (name, name))
  description = cursor.cursor.description
  headers = [k[0] for k in description]
  TableCls = create_table()
  for head in headers:
    TableCls.add_column(head, Col(head, column_html_attrs=dict(align="left")))
  items = cursor.fetchall()
  cursor.close()
  global CONTEXT
  CONTEXT['tables'] = TableCls(items, border=True)
  CONTEXT['p_name'] = name
  return redirect('/page1')

@app.route('/rank', methods = ["POST"])
def rank():
    mode = request.form['mode']
    if request.form['stat'] == 'Leaders of Season 2009-2010!':
      year = 2
    else:
      year = 1
    cursor = g.conn.execute(
    "SELECT p.full_name, t.name AS play_for,pf.%s FROM players p, play_for pf, teams_home t"
    " WHERE p.player_id=pf.player_id AND pf.season_id=%s AND pf.team_id=t.team_id "
    "ORDER BY pf.%s DESC LIMIT 5" % (mode, year, mode))
    description = cursor.cursor.description
    headers = [k[0] for k in description]
    TableCls = create_table()
    for head in headers:
      TableCls.add_column(head, Col(head, column_html_attrs=dict(align="left")))
    global CONTEXT
    items = cursor.fetchall()
    CONTEXT['tables'] = TableCls(items, border=True)
    CONTEXT['sel'] = mode
    cursor.close()
    return redirect('/page1')

@app.route('/clear1', methods = ["POST"])
def clear1():
  global CONTEXT
  CONTEXT={}
  return redirect('/page1')


# page2 -- teams
@app.route('/page2')
def page2():
  return render_template("team.html", **CONTEXT2)

@app.route('/clear2', methods = ["POST"])
def clear2():
  global CONTEXT2
  CONTEXT2={}
  return redirect('/page2')

@app.route('/team', methods = ["POST"])
def team():
  name = request.form['name']
  year = 1
  stat =  request.form['stat']
  global CONTEXT2
  if stat == 'Head Coach':
    cursor = g.conn.execute(
      "SELECT head.name, teach.start_date, teach.end_date "
      "FROM teams_home t, teach, head WHERE "
      "t.name='%s' AND t.team_id=teach.team_id AND teach.coach_id=head.coach_id "
      "ORDER BY teach.start_date DESC" % name)
    description = cursor.cursor.description
    headers = [k[0] for k in description]
    TableCls = create_table()
    for head in headers:
      TableCls.add_column(head, Col(head, column_html_attrs=dict(align="left")))
    items = cursor.fetchall()
    cursor.close()
    CONTEXT2['tables'] = TableCls(items, border=True)
    CONTEXT2['tables2'] = ""
    CONTEXT2['tables3'] = ""
    CONTEXT2['tables4'] = ""
  elif stat == 'Roster of Season 2009-2010!' or stat == 'Roster of Season 2010-2011!':
    if stat == 'Roster of Season 2009-2010!':
      year = 2
    cursor = g.conn.execute(
      "SELECT p.full_name AS player_name, th.name AS team_name FROM players p, play_for pf, teams_home th"
      " WHERE p.player_id = pf.player_id AND pf.team_id = th.team_id AND th.name = '%s' AND pf.season_id=%s" % (name,year))
    description = cursor.cursor.description
    headers = [k[0] for k in description]
    TableCls = create_table()
    for head in headers:
      TableCls.add_column(head, Col(head, column_html_attrs=dict(align="left")))
    items = cursor.fetchall()
    cursor.close()
    CONTEXT2['tables'] = TableCls(items, border=True)
    CONTEXT2['tables2'] = ""
    CONTEXT2['tables3'] = ""
    CONTEXT2['tables4'] = ""
  else:
    if stat == "Team's top player in Season 2009-2010!":
      year = 2
    for p in [("pg_point", "tables"), ("pg_assist", "tables2"), ("pg_rebound", "tables3"), ("pg_block", "tables4")]:
      cursor = g.conn.execute("SELECT p.full_name AS name, pf.%s FROM "
        "players p, play_for pf, teams_home t "
        "WHERE p.player_id=pf.player_id AND pf.team_id = t.team_id AND t.name = '%s' "
        "AND pf.season_id=%d ORDER BY pf.%s DESC LIMIT 5" % (p[0], name, year, p[0]));
      description = cursor.cursor.description
      headers = [k[0] for k in description]
      TableCls = create_table()
      for head in headers:
        TableCls.add_column(head, Col(head, column_html_attrs=dict(align="left")))
      items = cursor.fetchall()
      cursor.close()
      CONTEXT2[p[1]] = TableCls(items, border=True)
  CONTEXT2['team_name'] = name
  CONTEXT2['year'] = stat
  return redirect('/page2')

# seasons and other
@app.route('/page3')
def page3():
  return render_template("season.html", **CONTEXT3)

@app.route('/avgp', methods = ["POST"])
def avgp():
  year = int(request.form['s1']) 
  cursor = g.conn.execute(
  "SELECT t.name AS Team_Name, t.conference, t.division, CAST(AVG(par.point) AS decimal(18,2)) Points_Per_Game "
  "FROM teams_home t, participate par, games_in g "
  "WHERE t.team_id = par.team_id AND g.game_id = par.game_id AND g.season_id = %d "
  "GROUP BY t.team_id, t.conference, t.division ORDER BY AVG(par.point) DESC" % year)
  description = cursor.cursor.description
  headers = [k[0] for k in description]
  TableCls = create_table()
  for head in headers:
    TableCls.add_column(head, Col(head, column_html_attrs=dict(align="left")))
  global CONTEXT
  items = cursor.fetchall()
  CONTEXT3['tables'] = TableCls(items, border=True)
  CONTEXT3['sel1'] = str(year)
  cursor.close()
  return redirect('/page3')

@app.route('/win', methods = ["POST"])
def win():
  year = int(request.form['s2'])
  cursor = g.conn.execute(
  "SELECT t.name AS Team_Name, t.conference, t.division, "
  "CAST(COUNT(CASE WHEN par.result THEN 1 END) * 1.0/COUNT(t.team_id) AS decimal(18,2)) AS Rate_of_Winning "
  "FROM teams_home t, participate par, games_in g "
  "WHERE t.team_id = par.team_id AND g.game_id = par.game_id AND g.season_id = %d "
  "GROUP BY t.name, t.conference, t.division ORDER BY COUNT(CASE WHEN par.result THEN 1 END) * 1.0/COUNT(t.team_id) "
  "DESC" % year)
  description = cursor.cursor.description
  headers = [k[0] for k in description]
  TableCls = create_table()
  for head in headers:
    TableCls.add_column(head, Col(head, column_html_attrs=dict(align="left")))
  global CONTEXT
  items = cursor.fetchall()
  CONTEXT3['tables'] = TableCls(items, border=True)
  CONTEXT3['sel2'] = str(year)
  cursor.close()
  return redirect('/page3')

@app.route('/margin', methods = ["POST"])
def margin():
  year = int(request.form['s3'])
  cursor = g.conn.execute(
  "SELECT allwin2.name, allwin2.opposite, allwin2.Fight_at_home, allwin2.most_difference AS largest_win_margin, allwin2.game_date "
  "FROM (SELECT allwin.name ,MAX(allwin.most_difference) AS valuechoice "
  "FROM (SELECT tw1.name, tt1.name AS opposite, True AS Fight_at_home, homewin.most_difference, g1.game_date "
  "FROM (SELECT t1.team_id , Max(par1.point - par2.point) AS most_difference "
  "FROM teams_home t1,teams_home t2, participate par1, participate par2, games_in g "
  "WHERE t1.team_id = par1.team_id AND t2.team_id = par2.team_id And g.game_id = par1.game_id And g.game_id = par2.game_id AND g.season_id = {0} AND g.home_id = t1.team_id And g.guest_id = t2.team_id And par1.result = True "
  "GROUP BY t1.team_id) AS homewin, games_in g1, teams_home tt1, participate parr1, participate parr2, teams_home tw1 "
  "WHERE homewin.team_id = g1.home_id AND homewin.team_id = parr1.team_id AND g1.guest_id = tt1.team_id AND tt1.team_id = parr2.team_id AND g1.season_id = {0} AND (parr1.point - parr2.point = homewin.most_difference) AND tw1.team_id = homewin.team_id AND parr1.game_id = g1.game_id AND parr2.game_id = g1.game_id "
  "UNION SELECT tw2.name, tt2.name AS opposite, False AS Fight_at_home, guestwin.most_difference, g2.game_date "
  "FROM (SELECT t4.team_id , Max(par4.point - par3.point) AS most_difference "
  "FROM teams_home t3,teams_home t4, participate par3, participate par4, games_in gg "
  "WHERE t3.team_id = par3.team_id AND t4.team_id = par4.team_id And gg.game_id = par3.game_id And gg.game_id = par4.game_id AND gg.season_id = {0} AND gg.home_id = t3.team_id And gg.guest_id = t4.team_id And par4.result = True "
  "GROUP BY t4.team_id) AS guestwin, games_in g2, teams_home tt2, participate parr3, participate parr4, teams_home tw2 "
  "WHERE guestwin.team_id = g2.guest_id AND guestwin.team_id = parr4.team_id AND g2.home_id = tt2.team_id AND tt2.team_id = parr3.team_id AND g2.season_id = {0} AND (parr4.point - parr3.point = guestwin.most_difference) AND tw2.team_id = guestwin.team_id AND parr3.game_id = g2.game_id AND parr4.game_id = g2.game_id) AS allwin "
  "GROUP BY allwin.name) AS allwinchoice, "
  "(SELECT tw1.name, tt1.name AS opposite, True AS Fight_at_home, homewin.most_difference, g1.game_date "
  "FROM (SELECT t1.team_id , Max(par1.point - par2.point) AS most_difference "
  "FROM teams_home t1,teams_home t2, participate par1, participate par2, games_in g "
  "WHERE t1.team_id = par1.team_id AND t2.team_id = par2.team_id And g.game_id = par1.game_id And g.game_id = par2.game_id AND g.season_id = {0} AND g.home_id = t1.team_id And g.guest_id = t2.team_id And par1.result = True "
  "GROUP BY t1.team_id) AS homewin, games_in g1, teams_home tt1, participate parr1, participate parr2, teams_home tw1 "
  "WHERE homewin.team_id = g1.home_id AND homewin.team_id = parr1.team_id AND g1.guest_id = tt1.team_id AND tt1.team_id = parr2.team_id AND g1.season_id = {0} AND (parr1.point - parr2.point = homewin.most_difference) AND tw1.team_id = homewin.team_id AND parr1.game_id = g1.game_id AND parr2.game_id = g1.game_id "
  "UNION SELECT tw2.name, tt2.name AS opposite, False AS Fight_at_home, guestwin.most_difference, g2.game_date "
  "FROM (SELECT t4.team_id , Max(par4.point - par3.point) AS most_difference "
  "FROM teams_home t3,teams_home t4, participate par3, participate par4, games_in gg "
  "WHERE t3.team_id = par3.team_id AND t4.team_id = par4.team_id And gg.game_id = par3.game_id And gg.game_id = par4.game_id AND gg.season_id = {0} AND gg.home_id = t3.team_id And gg.guest_id = t4.team_id And par4.result = True "
  "GROUP BY t4.team_id) AS guestwin, games_in g2, teams_home tt2, participate parr3, participate parr4, teams_home tw2 "
  "WHERE guestwin.team_id = g2.guest_id AND guestwin.team_id = parr4.team_id AND g2.home_id = tt2.team_id AND tt2.team_id = parr3.team_id AND g2.season_id = {0} AND (parr4.point - parr3.point = guestwin.most_difference) AND tw2.team_id = guestwin.team_id AND parr3.game_id = g2.game_id AND parr4.game_id = g2.game_id) AS allwin2 "
  "Where allwinchoice.name = allwin2.name AND allwinchoice.valuechoice = allwin2.most_difference".format(year))
  description = cursor.cursor.description
  headers = [k[0] for k in description]
  TableCls = create_table()
  for head in headers:
    TableCls.add_column(head, Col(head, column_html_attrs=dict(align="left")))
  global CONTEXT
  items = cursor.fetchall()
  CONTEXT3['tables'] = TableCls(items, border=True)
  CONTEXT3['sel3'] = str(year)
  cursor.close()
  return redirect('/page3')

@app.route('/coach', methods = ["POST"])
def coach():
  cursor = g.conn.execute(
    "SELECT h.name, CAST(COUNT(CASE WHEN par.result THEN 1 END) * 1.0/COUNT(par.team_id) AS decimal(18,2)) AS Rate_of_Winning "
    "FROM head h, teach t, teams_home th, participate par, games_in g "
    "WHERE h.coach_id = t.coach_id AND t.team_id = th.team_id AND th.team_id = par.team_id AND (g.home_id = th.team_id OR g.guest_id = th.team_id) "
    "AND g.game_date between t.start_date and t.end_date "
    "GROUP BY h.name ORDER BY COUNT(CASE WHEN par.result THEN 1 END) * 1.0/COUNT(par.team_id) DESC")
  description = cursor.cursor.description
  headers = [k[0] for k in description]
  TableCls = create_table()
  for head in headers:
    TableCls.add_column(head, Col(head, column_html_attrs=dict(align="left")))
  global CONTEXT
  items = cursor.fetchall()
  CONTEXT3['tables'] = TableCls(items, border=True)
  cursor.close()
  return redirect('/page3')

@app.route('/sponsor', methods = ["POST"])
def sponsor():
  sp=request.form['s4']
  cursor = g.conn.execute(
    "SELECT p.full_name AS Name, p.position, CAST(AVG(pf.pg_point) AS decimal(18,2)) Points_Per_Game,CAST(AVG(pf.pg_assist) "
    "AS decimal(18,2)) Assist_Per_Game,CAST(AVG(pf.pg_rebound) AS decimal(18,2)) Rebound_Per_Game "
    "FROM companys c, sponsors s, play_for pf, players p "
    "WHERE c.comp_id = s.comp_id AND s.player_id = pf.player_id AND pf.player_id = p.player_id AND c.name = '%s' "
    "GROUP BY p.player_id, p.full_name, p.position "
    "HAVING AVG(pf.pg_point) > 10 AND AVG(pf.pg_assist) > 4 AND AVG(pf.pg_rebound) > 4" % sp)
  description = cursor.cursor.description
  headers = [k[0] for k in description]
  TableCls = create_table()
  for head in headers:
    TableCls.add_column(head, Col(head, column_html_attrs=dict(align="left")))
  global CONTEXT
  items = cursor.fetchall()
  CONTEXT3['tables'] = TableCls(items, border=True)
  CONTEXT3['sel4'] = sp
  cursor.close()
  return redirect('/page3')

@app.route('/stadium', methods = ["POST"])
def stadium():
  cursor = g.conn.execute(
    "SELECT s.name, s.capacity, s.city, th.name AS team_name, s.sponsor "
    "FROM stadiums s, teams_home th "
    "WHERE s.stdm_id = th.stdm_id")
  description = cursor.cursor.description
  headers = [k[0] for k in description]
  TableCls = create_table()
  for head in headers:
    TableCls.add_column(head, Col(head, column_html_attrs=dict(align="left")))
  global CONTEXT
  items = cursor.fetchall()
  CONTEXT3['tables'] = TableCls(items, border=True)
  cursor.close()
  return redirect('/page3')

@app.route('/clear3', methods = ["POST"])
def clear3():
  global CONTEXT3
  CONTEXT3={}
  return redirect('/page3')

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
