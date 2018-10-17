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
import json
import datetime as dt

from StocksAutoTrader import StocksAutoTrader


if __name__ == '__main__':

    # Set timezone
    set(pytz.all_timezones_set)

    # Read configuration file
    try:
        with open('../config/config.json', 'r') as file:
            config = json.load(file)
    except IOError:
        logging.error("Configuration file not found!")
        exit()

    # Define the global logging settings
    debugLevel = logging.DEBUG if config['general']['debug_log'] else logging.INFO
    # If enabled define log file filename with current timestamp
    if config['general']['enable_log']:
        log_filename = config['general']['log_file']
        time_str = dt.datetime.now().isoformat()
        time_suffix = time_str.replace(':', '_').replace('.', '_')
        log_filename = log_filename.replace('{t}', time_suffix)
        logging.basicConfig(filename=log_filename,
                        level=debugLevel,
                        format="[%(asctime)s] %(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=debugLevel,
                        format="[%(asctime)s] %(levelname)s: %(message)s")



    robot = StocksAutoTrader(config)
    robot.start(sys.argv)
