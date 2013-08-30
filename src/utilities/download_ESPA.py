###############################################################################
# Script to download a set of Landsat images from ESPA given a valid order ID 
# and the email that placed the ESPA order.
###############################################################################

import os
import sys
import re
import argparse # Requires Python 2.7 or above
import urllib

def main():
    parser = argparse.ArgumentParser(description='Download a completed ESPA order given an email address and ESPA order ID')
    parser.add_argument("email", metavar="email", type=str, default=None,
            help='Email address used to place the order')
    parser.add_argument("order_ID", metavar="order_ID", type=str, default=None,
            help='ESPA order ID')
    parser.add_argument("--output_folder", metavar="output_folder", type=str, default=None,
            help='Folder to save output data (defaults to working directory)')
    args = parser.parse_args()

    email = args.email
    email_re = re.compile('^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$', re.IGNORECASE)
    if not email_re.match(email):
        raise IOError('%s does not appear to be a valid email address'%email)

    order_ID = args.order_ID
    order_ID_re = re.compile('^[0-9]{13}$')
    if not order_ID_re.match(order_ID):
        raise IOError('%s does not appear to be a valid ESPA order ID'%order_ID)

    if not args.output_folder:
        output_folder = os.getcwd()
    else:
        output_folder = args.output_folder

    print 'Saving downloads to %s'%output_folder

    email_noat = re.sub('@', '%40', email)
    f = urllib.urlopen("http://espa.cr.usgs.gov/status/%s-%s"%(email_noat, order_ID))
    espa_page = f.read()
    f.close()

    # Parse file for download links
    url_re = re.compile('http:\/\/espa\.cr\.usgs\.gov\/orders\/%s-%s/L[ET][0-9]{14}-SC[0-9]{14}\.tar\.gz'%(email, order_ID))
    urls = []
    for line in espa_page.splitlines():
        url = url_re.search(line)
        if url:
            urls.append(url.group())
    urls = list(set(urls))

    # Progress bar code is from: http://bit.ly/1a5JW7H
    global progress_text # global variable to be used in dlProgress
    def dlProgress(count, blockSize, totalSize):
          percent = int(count * blockSize * 100 / totalSize)
          sys.stdout.write("\r" + progress_text + "...%d%%"%percent)
          sys.stdout.flush()
    
    for n in xrange(len(urls)):
        url = urls[n]
        filename = os.path.basename(url)
        progress_text = 'File %s of %s: %s'%(n + 1, len(urls), filename)
        urllib.urlretrieve(url, os.path.join(output_folder, filename), reporthook=dlProgress)

    print 'Completed %s files'%len(urls)
    
if __name__ == "__main__":
    sys.exit(main())
