###############################################################################
# Script to download a set of Landsat images from ESPA given a valid order ID 
# and the email that placed the ESPA order.
###############################################################################

import os
import sys
import re
import argparse # Requires Python 2.7 or above
import hashlib
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
        global progress_text # global variable to be used in dlProgress
        percent = int(count * blockSize * 100 / totalSize)
        sys.stdout.write("\r" + progress_text + "...%d%%"%percent)
        sys.stdout.flush()

    def get_md5_for_file(file, block_size=2**20):
        f = open(file, 'rb')
        md5 = hashlib.md5()
        while True:
            data = f.read(block_size)
            if not data:
                break
            md5.update(data)
        f.close()
        return md5.hexdigest()

    def check_ESPA_checksum(remote_url, local_url):
        f = urllib.urlopen(re.sub('\.tar\.gz$', '.cksum', remote_url))
        espa_checksum_file = f.read()
        f.close()
        espa_checksum_file = espa_checksum_file.split()
        # TODO: Figure out WHAT checksum ESPA is using...
        #if espa_checksum_file[0] != get_md5_for_file(local_url):
        #    return 1
        if int(espa_checksum_file[1]) != os.path.getsize(local_url):
            return 1
        else:
            return 0

    def download_ESPA_file(url, output_path):
        global progress_text # global variable to be used in dlProgress
        progress_text = 'File %s of %s: %s'%(n + 1, len(urls), filename)
        urllib.urlretrieve(url, output_path, reporthook=dlProgress)
        return check_ESPA_checksum(url, output_path)

    successes = 0
    failures = 0
    skips = 0
    for n in xrange(len(urls)):
        url = urls[n]
        filename = os.path.basename(url)
        output_path = os.path.join(output_folder, filename)
        if os.path.exists(output_path):
            if check_ESPA_checksum(url, output_path):
                print 'Warning: %s exists but has bad checksum - re-downloading file'%output_path
            else:
                print 'Warning: %s exists and has good checksum - skipping download'%output_path
                skips += 1
                continue
        if download_ESPA_file(url, output_path) == 0:
            successes += 1
        else:
            print 'Warning: %s downloaded with bad checksum'%output_path
            failures += 1
        print

    print '%s files succeeded. %s files skipped. %s files failed.'%(successes, skips, failures)

if __name__ == "__main__":
    sys.exit(main())
