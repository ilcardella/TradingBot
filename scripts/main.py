###############################################################################
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE AND
# NON-INFRINGEMENT. IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR ANYONE
# DISTRIBUTING THE SOFTWARE BE LIABLE FOR ANY DAMAGES OR OTHER LIABILITY,
# WHETHER IN CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
###############################################################################

import pytz
import logging
import sys

from Utils import *
from StocksAutoTrader import StocksAutoTrader
from Strategies.FAIG_iqr import FAIG_iqr
from Strategies.SimpleMACD import SimpleMACD

if __name__ == '__main__':

    set(pytz.all_timezones_set)

    #config = ConfigurationManager('../config/config.json')
    try:
        with open('../config/config.json', 'r') as file:
            config = json.load(file)
    except IOError:
        file = open(filepath, 'w')
        # TODO write the template config file with default values
        config = json.load(file)

    debugLevel = logging.DEBUG if config['general']['debug_log'] else logging.INFO
    logging.basicConfig(#filename=logfile_name,
                        level=debugLevel,
                        format="[%(asctime)s] %(levelname)s: %(message)s")

    ##################################################
    # Define the strategy to use here
    ##################################################

    # Create the strategy
    #strategy = FAIG_iqr(config)
    strategy = SimpleMACD(config)

    ###################################################
    ###################################################

     # TODO start on a separate thread
    robot = StocksAutoTrader(config)
    robot.start(sys.argv, strategy)

    # TODO for the future
    # Create other trader robots (currency, crypto, index, etc.)
    # Start them on different threads

    # call thread.join on all of them and wait

