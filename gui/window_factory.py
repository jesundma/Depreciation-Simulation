import tkinter as tk
from tkinter import ttk
from gui.status_window import StatusWindow

class WindowFactory:
    @staticmethod
    def create_status_window(title, message):
        """
        Creates and returns a StatusWindow with a given title and message.
        """
        status_window = StatusWindow(title)
        status_window.text_area.insert(tk.END, message)
        return status_window

    @staticmethod
    def create_generic_window(title, geometry, widgets):
        """
        Creates a generic Toplevel window with the specified title, geometry, and widgets.
        :param title: Title of the window.
        :param geometry: Geometry of the window (e.g., "400x300").
        :param widgets: A list of widget creation functions to add to the window.
        """
        window = tk.Toplevel()
        window.title(title)
        window.geometry(geometry)

        for widget in widgets:
            widget(window)

        return window

    @staticmethod
    def create_generic_window_with_widgets(title, geometry, widget_creators):
        """
        Creates a generic Toplevel window with the specified title, geometry, and widgets.
        Returns the window and a dictionary of created widgets.
        :param title: Title of the window.
        :param geometry: Geometry of the window (e.g., "400x300").
        :param widget_creators: A list of tuples (key, widget creation function).
        """
        window = tk.Toplevel()
        window.title(title)
        window.geometry(geometry)

        widgets = {}
        for key, creator in widget_creators:
            widgets[key] = creator(window)

        return window, widgets
