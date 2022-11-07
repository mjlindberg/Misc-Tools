#!/usr/bin/env python3

"""
PubMedScraper

Searches PubMed and pulls out abstracts.
Then finds the PDF on Sci-Hub if available.

To do:
Fix import error trapping
Add error trapping for empty search
Add error trapping for Urllib timing out/SSL issues
Pointless - setdir? saving output?

"""
from os import mkdir, listdir, chdir, system
from sys import exit

try:
    import urllib.request
except ImportError:
    system("pip install urllib")
    import urllib.request
try:
    import bs4
except ImportError:
    system("pip install bs4")
    system("pip install lxml")
    import bs4
try:
    from Bio import Entrez
except ImportError:
    system("pip install biopython")
    from Bio import Entrez


# Simple function to format text with various styles.
def format_font(some_text, text_color='green', bg_color='black', text_style='none'):

    text_colors = {"black": '30', "red": '31', "green": '32', "yellow": '33',
                   "blue": '34', "purple": '35', "cyan": '36', "white": '37'}
    bg_colors = {"black": '40', "red": '41', "green": '42', "yellow": '43',
                 "blue": '44', "purple": '45', "cyan": '46', "white": '47'}
    text_styles = {"none": '0', "bold": '1', "underline": '2', "italicized": '3', "negative2": '5'}

    color_start = "\033[" + text_styles[text_style] + ";" + \
                  text_colors[text_color] + ";" + bg_colors[bg_color] + "m"
    color_end = "\033[0m"

    return color_start + some_text + color_end


def set_dir(argument=None):

    root_path = "./"
    folder = "PubMed_Literature"
    full_path = root_path + folder

    if argument is not None:
        folder = input("Folder name (will be made in current directory): ")

    if folder not in listdir("."):
        mkdir(full_path)
    else:
        print("Folder already exists.")

    chdir(full_path)


def search(query):
    Entrez.email = 'katieup69@gmail.com'
    handle = Entrez.esearch(db='pubmed',
                            sort='relevance',
                            retmax=input("Number of articles to fetch: "),
                            retmode='xml',
                            term=query)
    results = Entrez.read(handle)
    return results


def fetch_details(id_list):
    ids = ','.join(id_list)
    Entrez.email = 'katieup69@gmail.com'
    handle = Entrez.efetch(db='pubmed',
                           retmode='xml',
                           id=ids)
    results = Entrez.read(handle)
    return results


def initialize():
    print("\n"+"*"*100+"\n"+"*"*34+format_font("PubMed Abstract Fetcher - v.1.01", "blue", "white")+
          "*"*34+"\n"+"*"*100+"\n")
    print("Welcome to the "+format_font("PubMed",text_color="yellow",bg_color="blue")+" literature finder.\n\n")

    #search_term1 = input("Search query in relation to annexin-A1 (e.g. lupus): ")
    # search_term1_strict = "("+input()+")"
    #search_term2 = "(annexin A1)"
    # search_query = ... + " NOT (annexin V)" - not needs to include annexin A1 to not filter out
    #search_query = search_term1 + " AND " + search_term2
    search_query = input("Search query: ")

    results = search(search_query)
    search_id_list = results['IdList']
    papers = fetch_details(search_id_list)  # could be simplified: fetch_details(search(search_query)['IdList'])

    pubmedlist = list(papers["PubmedArticle"])

    return papers


def get_article_attributes(root):  # Make dict of {PMID:article}?
    root_mc = root['MedlineCitation']
    root_pmd = root['PubmedData']

    article_title = root_mc['Article']['ArticleTitle']
    keywords = root_mc["KeywordList"]
    pubmed_id = root_mc['PMID']
    date_published = root_pmd['History'][0]['Year']
    #authors = "null"
    if 'AuthorList' in root_mc['Article'].keys():
        authors = root_mc['Article']['AuthorList'][0]['LastName']+" et al. ("+date_published+")" # NEED TO ERROR TRAP
    else:
        authors = "("+date_published+")"

    if 'Abstract' in root_mc['Article'].keys():
        abstract = "".join(root_mc['Article']['Abstract']['AbstractText'])
    else:
        abstract = "No abstract found."

    if len(root_mc['Article']['ELocationID']) == 1:
        elocation_id = root_mc['Article']['ELocationID'][0]
    elif len(root_mc['Article']['ELocationID']) > 1:
        elocation_id = root_mc['Article']['ELocationID'][1]
        for i in range(len(root_mc['Article']['ELocationID'])):
            #print(root_mc['Article']['ELocationID'][i])  #Remove
            if "10." in root_mc['Article']['ELocationID'][i]:
                elocation_id = root_mc['Article']['ELocationID'][i]

    else:
        elocation_id = "NONE"

    output = \
        format_font(article_title, "green")+"\n"+authors+"\nPMID: " + \
        pubmed_id+"\n\n"+abstract+"\n\n"+"Other journal ID: " + \
        elocation_id+"\n"+("_"*100)+"\n"

    return [output, date_published, elocation_id, pubmed_id]


def print_results(papers):

    articles = []

    for paper in papers['PubmedArticle']:
        article_outline = get_article_attributes(paper)
        articles.append(article_outline)
    
    articles_found = '\n'+str(len(papers['PubmedArticle']))+" article(s) found."+'\n'

    print(format_font(articles_found,"yellow","black","italicized"))
    
    articles.sort(key=lambda x: x[1], reverse=True)
    article_num = 1

    go_mode = False  # Flag for skipping input letting you to go through articles one by one
    skip = False

    for article in articles:
        if not skip:
            print((str(article_num)+": "), article[0])
        if "NONE" not in article[2]:
            article.append(sci_hub_scraper(article[2]))  # This appends the HTML source of Sci-Hub page to article list
        else:
            article.append(sci_hub_scraper(("https://www.ncbi.nlm.nih.gov/pubmed/"+article[3])))

        article_num += 1

        if not go_mode:  # Add ability to skip to end w/ article URLs? Maybe make a fxn.
            continue_mode = input('[NEXT]\n')
        if continue_mode.lower() in ["quit","exit"] and not go_mode:
            exit("Quitting...")
        elif continue_mode.lower() in ["go"]:
            go_mode = True
        elif continue_mode.lower() in ["skip"]: #Causing SSL errors in Urlopen
            skip = True
            go_mode = True
        elif continue_mode.lower() in ["pdf"]:
            print("PDF: ",article[4][1])
            if input("Copy URL to clipboard?\t").lower() in ["yes","y"]:
                system("echo '%s' | pbcopy" % article[4][1])
                print(format_font("URL copied to clipboard.\n\n",text_style="italicized", text_color="yellow"))



        '''
        if continue_mode.lower() in "skip":
            for each in articles:
                if ".pdf" in each[4][1][:-10]:
                    print(each[3], ": ", each[4][1][:-10])  # len(each[4][0]) - if 0, no PDF/page found
                else:
                    print(each[3], ": ", each[4][1])
            exit("Quitting...")
        '''
        # Add ability to immediately get Scihub URL for current paper
        # Add ability to get unsorted papers!

    print("\nNumber of articles found: ", len(papers['PubmedArticle']), "\n")
    print("  PMID")
    for each in articles: #Articles structure: 0 - Abstract & details ; 1 - date?; 2 - ; 3 - ; 4 -
        if ".pdf" in each[4][1][:-10]:
            print(each[3], ": ", each[4][1][:-10])  # len(each[4][0]) - if 0, no PDF/page found
        else:
            print(each[3], ": ", each[4][1])


def write_output(papers, silent=False, write=False):  # Integrate w/ above so saved list is also sorted.

    if silent is False:
        print_results()

    if write is True:
        i = 1
        outfile = open((search_term1.replace(" ", "_")+"-ANXA1_articles.txt"), "w")
        for paper in papers['PubmedArticle']:
            outfile.write(str(i)+". "+get_article_attributes(paper)+"\n")
            i += 1


def grab_url(url):
    request = urllib.request.Request(url)
    opener = urllib.request.build_opener()
    response = opener.open(request)

    # print(response.code)
    # print(response.headers)
    html = response.read()
    soup = bs4.BeautifulSoup(html, features="lxml")
    if soup.find(id='pdf'):
        pdf_url = soup.find(id='pdf').get('src')
    elif "sci-hub" not in response.url:
        pdf_url = response.url
    else:
        pdf_url = "No PDF found"
    return soup.prettify(), pdf_url


def sci_hub_scraper(article_url):  # Will need a try statement w/ base_url; else use mirror.
    #https://whereisscihub.now.sh/ - Working mirrors for Sci-Hub; none working - is it blocked in the UK?
    #base_url = "https://sci-hub.ink/"
    base_url = "https://sci-hub.se/" #- Stopped working as of 01/05/19?
    #base_url = "https://sci-hub.tw/" # Super slow? Also down?
    full_url = base_url + article_url
    print(format_font("SCI-HUB GRABBING...\n", text_style="italicized", text_color="white", bg_color="black"))
    return grab_url(full_url)


def get_pub_med_url(PMID):
    pub_med_url = ""
    return pub_med_url


print('\n')

#set_dir()
output = initialize()
print_results(output)
# write_output(output, write=True)

# TO DO:
# fxn for pulling each paper from sci-hub -> ISSUE: CAPTCHA (can I download paper w/o it?)
# assign article names/abstract/etc. so we know what each PMID refers to - DONE
# times cited?
#  Next, using BS4 - pull HTML source of each Scihub page, find link of PDF, and download. - Fix for #1
