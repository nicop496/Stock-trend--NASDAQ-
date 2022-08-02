from pandas import Series
from get_data import read_csv, get_companies_list

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label


class InputScreen(BoxLayout):
    PER_PAGE = 150
    COMPANIES_DF = get_companies_list()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.show_new_df(self.COMPANIES_DF)
    
        # Create country and sector filters
        self.filter_widgets = {}
        def country_and_sector(title):
            widgets = []
            for name in sorted(self.df[title].drop_duplicates().dropna().values):
                checkbox = CheckBox(size_hint_x=.2)
                label = Label(text=name, halign='left', height='20dp')
                label.text_size = label.size
                box = BoxLayout(size_hint_y=None, height='20dp')
                box.add_widget(checkbox)
                box.add_widget(label)
                self.ids[title.lower() + '_filters_container'].add_widget(box)
                widgets.append(box.children)
            self.filter_widgets[title] = widgets
        country_and_sector('Country')
        country_and_sector('Sector')
        
    def show_new_df(self, df):
        # Define the new dataframe
        self.df = df

        # Create new indexes and pages
        self.current_page_idx = 0
        self.indexes = []
        self.pages = [ScrollViewContainer()]
        
        rows_amount = self.df.shape[0]

        for idx in range(self.PER_PAGE, rows_amount, self.PER_PAGE):
            self.indexes.append((idx-self.PER_PAGE, idx))
            self.pages.append(ScrollViewContainer())
        self.indexes.append((rows_amount - rows_amount%self.PER_PAGE, rows_amount))

        self.go_to_page(self.current_page_idx)

    def go_to_page(self, page_idx):
        # Remove current page
        old_page = self.ids.page_container.children[0]
        self.ids.page_container.remove_widget(old_page)
        
        # Load new page widgets
        start_idx = self.indexes[page_idx][0]
        end_idx = self.indexes[page_idx][1]
        symbols_list = self.df.iloc[start_idx:end_idx].index
        
        for symbol in symbols_list:
            name = self.df.loc[symbol].Name
            self.pages[page_idx].add_widget(CompanyWidget(symbol, name))
        
        # Add page
        self.ids.page_container.add_widget(self.pages[page_idx])
        self.current_page_idx = page_idx

        # Set disabled property for previous and next page buttons
        self.ids.previous_page_btn.disabled = self.current_page_idx == 0
        self.ids.next_page_btn.disabled = self.current_page_idx  == len(self.pages) - 1

        # Set page info
        self.ids.page_info_label.text = f'Page {page_idx} of {len(self.pages)}'

        # Scroll up if there are companies
        if symbols_list.any():
            self.ids.page_container.scroll_to(self.pages[page_idx].children[-1])

    def apply_filters(self):
        new_df = self.COMPANIES_DF
        
        # Search bar
        def search_bar(df):
            msg = self.ids.search_bar.text
            if not msg:
                return
            pattern = f'(?:{msg.replace(" ", "|")})'
            return df['Name'].str.contains(pattern, case=False)

        # Market cap
        def market_cap(min_or_max:str, df):
            txt_input_value = self.ids[min_or_max + '_marketcap'].text
            if not txt_input_value:
                return
            value = int(txt_input_value)
            if min_or_max == 'min':
                return df['Market Cap'] >= value
            if min_or_max == 'max':
                return df['Market Cap'] <= value

        # Country
        def country_and_sector(title, df):
            keywords = [label.text for label, checkbox in self.filter_widgets[title] if checkbox.active]
            if not keywords:
                return
            pattern = f'(?:{"|".join(keywords)})'
            return df[title].str.contains(pattern)
        
        # Get the filters
        filter_series = list(filter(lambda s: type(s) == Series, [
            search_bar(new_df),
            market_cap("min", new_df), 
            market_cap("max", new_df), 
            country_and_sector("Country", new_df), 
            country_and_sector("Sector", new_df),
        ]))
        # Return the complete companies list if there are no filters
        if not filter_series:
            return self.show_new_df(new_df) 

        # Otherwise, get and then show the new filtered dataframe
        super_filter = filter_series[0]
        for series in filter_series:
            super_filter = super_filter & series
        new_df = new_df[super_filter]
        self.show_new_df(new_df)


class CompanyWidget(BoxLayout):
    def __init__(self, symbol, name, **kwargs):
        super().__init__(**kwargs)
        self.ids.symbol_label.text = symbol
        self.ids.name_label.text = name


class FiltersWidget(BoxLayout):
    title = StringProperty()


class ScrollViewContainer(BoxLayout): 
    None


class MainApp(App):
    title = 'Stock Trend (NASDAQ)'
    def build(self):
        return InputScreen()


if __name__ == '__main__':
    MainApp().run()
