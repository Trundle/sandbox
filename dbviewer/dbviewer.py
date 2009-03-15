#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

"""
    dbviewer.py
    ~~~~~~~~~~~
    Ein simpler Datenbankbetrachter.

    Geschrieben 2008 von Andy S.
"""

import gtk
import sqlalchemy


class DatabaseViewerError(Exception):
    """Basis-Klasse für alle DatabaseViewer-Exceptions."""


def mysql_get_tables(engine):
    result = engine.execute(sqlalchemy.text('''
            SHOW TABLES;
        '''))
    tables = [r[0] for r in result]
    result.close()
    return tables

def sqlite_get_tables(engine):
    result = engine.execute(sqlalchemy.text('''
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name;
        '''))
    tables = [r.name for r in result]
    result.close()
    return tables

def get_tables(engine):
    """Gibt eine Liste mit allen Tabellennamen der Datenbank zurück."""
    if engine.url.drivername == 'sqlite':
        return sqlite_get_tables(engine)
    elif engine.url.drivername == 'mysql':
        return mysql_get_tables(engine)
    else:
        raise DatabaseViewerError('unsupported database type')


class Database(object):
    def __init__(self, url):
        self.engine = sqlalchemy.create_engine(url)
        self.meta = sqlalchemy.MetaData(self.engine)
        self.tables = [sqlalchemy.Table(table, self.meta, autoload=True)
                        for table in get_tables(self.engine)]

    def get_table(self, name):
        for table in self.tables:
            if table.name == name:
                return table
        raise Exception('unknown table')


class ViewerWindow(gtk.Window):
    def __init__(self, *args, **kwargs):
        gtk.Window.__init__(self, *args, **kwargs)
        self.connect('delete-event', lambda w, e: gtk.main_quit())
        self.set_title('Datenbankbetrachter (nicht verbunden)')

        vbox = gtk.VBox()
        self.add(vbox)

        # Menü erstellen
        self.create_ui()
        vbox.pack_start(self.ui.get_widget('/Menubar'), expand=False)

        hpaned = gtk.HPaned()
        vbox.pack_start(hpaned)

        # Tabellen-Treeview erstellen
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        hpaned.add1(sw)
        model = gtk.TreeStore(str)
        self.tables_treeview = gtk.TreeView(model)
        self.tables_treeview.connect('row-activated',
                                     self.on_row_activated)
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(u'Tabelle', renderer, text=0)
        self.tables_treeview.append_column(column)
        sw.add(self.tables_treeview)
        
        # Spalten-Treeview erstellen
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        hpaned.add2(sw)
        self.columns_treeview = gtk.TreeView()
        sw.add(self.columns_treeview)

    def create_ui(self):
        ag = gtk.ActionGroup('WindowActions')
        actions = (
                ('DatabaseMenu', None, '_Datenbank'),
                ('Connect', None, u'_Verbinden', None,
                    u'Mit Datenbank verbinden', self.on_connect),
                ('Quit', None, u'_Beenden', None,
                    u'Datenbankbetrachter beenden', gtk.main_quit),

                ('HelpMenu', None, '_Hilfe'),
                ('About', None, u'_Über', None,
                    u'Über Datenbankbetrachter', self.on_about)
            )
        ag.add_actions(actions)
        self.ui = gtk.UIManager()
        self.ui.insert_action_group(ag, 0)
        self.ui.add_ui_from_string('''
                <ui>
                    <menubar name='Menubar'>
                        <menu action='DatabaseMenu'>
                            <menuitem action='Connect' />
                            <menuitem action='Quit' />
                        </menu>
                        <menu action='HelpMenu'>
                            <menuitem action='About' />
                        </menu>
                    </menubar>
                </ui>
            ''')
        self.add_accel_group(self.ui.get_accel_group())

    def on_about(self, action):
        """Wird aufgerufen, wenn der Benutzer auf den Über-Menüpunkt
        geklickt hat und zeigt den Über-Dialog an."""
        dialog = gtk.MessageDialog(self,
                                   (gtk.DIALOG_MODAL |
                                    gtk.DIALOG_DESTROY_WITH_PARENT),
                                   gtk.MESSAGE_INFO,
                                   gtk.BUTTONS_OK,
                                   u'Datenbankbetrachter\n'
                                   u'Geschrieben 2008 von Andy S.')
        dialog.set_title(u'Über')
        dialog.run()
        dialog.destroy()

    def on_connect(self, action):
        """Wird aufgerufen, wenn der Benutzer auf den
        Verbinden-Menüpunkt klickt."""
        dialog = gtk.Dialog(u'Datenbank öffnen',
                            self,
                            (gtk.DIALOG_MODAL |
                             gtk.DIALOG_DESTROY_WITH_PARENT),
                            (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                             gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))
        dialog.vbox.pack_start(gtk.Label('URL der Datenbank:'))
        entry = gtk.Entry()
        entry.set_text('sqlite:////tmp/foo.db')
        dialog.vbox.pack_start(entry)
        dialog.show_all()
        response = dialog.run()
        dialog.destroy()
        if response != gtk.RESPONSE_ACCEPT:
            return
        try:
            self.load(entry.get_text())
        except sqlalchemy.exceptions.SQLAlchemyError, e:
            dialog = gtk.MessageDialog(self,
                                       (gtk.DIALOG_MODAL |
                                        gtk.DIALOG_DESTROY_WITH_PARENT),
                                       gtk.MESSAGE_ERROR,
                                       gtk.BUTTONS_OK,
                                       (u'Konnte die URL ' +
                                        entry.get_text() + 
                                        u' nicht öffnen (%s)' % e))
            dialog.run()
            dialog.destroy()
            return

    def load(self, url):
        self.database = Database(url)
        url = self.database.engine.url
        if url.password is not None:
            url = unicode(url).replace(':' + url.password, '', 1)
        else:
            url = unicode(url)
        self.set_title('Datenbankbetrachter (verbunden mit %s)' % url)
        self.load_database()

    def on_row_activated(self, treeview, path, column):
        model = treeview.get_model()
        iter_  = model.get_iter(path)
        table_name = model.get_value(iter_, 0)
        self.load_table(table_name)

    def load_database(self):
        model = self.tables_treeview.get_model()
        model.clear()
        for table in self.database.tables:
            iter_ = model.append(None)
            model.set_value(iter_, 0, table.name)

    def load_table(self, table_name):
        # Alte Spalten entfernen
        for column in self.columns_treeview.get_columns():
            self.columns_treeview.remove_column(column)

        table = self.database.get_table(table_name)
        model = gtk.TreeStore(*(str,) * len(table.columns))
        self.columns_treeview.set_model(model)
        # Spalten hinzufügen
        for i, column in enumerate(table.columns):
            renderer = gtk.CellRendererText()
            column = gtk.TreeViewColumn(column.name, renderer, text=i)
            column.set_resizable(True)
            column.set_sort_column_id(i)
            self.columns_treeview.append_column(column)
        # Daten laden
        result = self.database.engine.execute(table.select())
        for row in result:
            model.append(None, row)


if __name__ == '__main__':
    import sys
    viewer = ViewerWindow()
    if len(sys.argv) == 2:
        from os.path import exists
        uri = sys.argv[1]
        if exists(uri):
            uri = 'sqlite:///' + uri
        viewer.load(uri)
    viewer.show_all()
    gtk.main()
