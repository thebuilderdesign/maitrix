from web3 import Web3
from eth_account import Account
import requests
import json
import os
import time
import random
from pyfiglet import Figlet
from colorama import init, Fore, Back, Style

init(autoreset=True)

PROXY_FILE = "proxy.txt"  
# Load proxies from proxy.txt
def load_proxies():
    proxies = []
    if os.path.exists(PROXY_FILE):
        with open(PROXY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    proxies.append(line)
    return proxies

# Global proxy list
PROXIES = load_proxies()


def get_random_proxy():
    all_proxies = load_proxies()
    if not all_proxies:
        return None
    chosen = random.choice(all_proxies)
    return {
        "http": chosen,
        "https": chosen
    }


# RPC and Contract Configuration
RPC_URL = "https://sepolia-rollup.arbitrum.io/rpc"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Contract Addresses
ATH_TOKEN = Web3.to_checksum_address("0x1428444Eacdc0Fd115dd4318FcE65B61Cd1ef399")
MINT_CONTRACT = Web3.to_checksum_address("0x2cFDeE1d5f04dD235AEA47E1aD2fB66e3A61C13e")

STAKING_CONTRACTS = {
    'AUSD': {
        'address': "0x054de909723ECda2d119E31583D40a52a332f85c",
        'token_address': "0x78De28aABBD5198657B26A8dc9777f441551B477"
    },
    'USDe': {
        'address': "0x3988053b7c748023a1aE19a8ED4c1Bf217932bDB",
        'token_address': "0xf4BE938070f59764C85fAcE374F92A4670ff3877" 
    },
    'LVLUSD': {
        'address': "0x5De3fBd40D4c3892914c3b67b5B529D776A1483A",
        'token_address': "0x8802b7bcF8EedCc9E1bA6C20E139bEe89dd98E83" 
    }
}

# ABIs
STAKING_ABI = json.loads('[{"inputs":[{"internalType":"uint256","name":"_tokens","type":"uint256"}],"name":"stake","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_user","type":"address"}],"name":"getUserStakeBalance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]')
ERC20_ABI = json.loads('[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"}]')

def print_header():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(Fore.WHITE + r"""
          

 _         _                     _                    
| |       | |                   | |                   
| |_ _   _| | ____ _ _ __   __ _| |_ _   _ _ __ _   _ 
| __| | | | |/ / _` | '_ \ / _` | __| | | | '__| | | |
| |_| |_| |   < (_| | | | | (_| | |_| |_| | |  | |_| |
 \__|\__,_|_|\_\__,_|_| |_|\__, |\__|\__,_|_|   \__,_|
                            __/ |                     
                           |___/                      

          """)
    print(Fore.GREEN + Style.BRIGHT + "Themaitrix Auto bot")
 

def load_private_keys():
    if not os.path.exists("privatekey.txt"):
        print(Fore.RED + "Error: privatekey.txt not found!")
        exit()
    
    with open("privatekey.txt", "r") as f:
        keys = [line.strip() for line in f.readlines() if line.strip()]
    
    if not keys:
        print(Fore.RED + "Error: No private keys found in privatekey.txt!")
        exit()
    
    return keys

def claim_faucet(private_key, faucet_type, proxies):
    account = Account.from_key(private_key)
    address = account.address
    
    endpoints = {
        'maitrix': 'https://app.x-network.io/maitrix-faucet/faucet',
        'usde': 'https://app.x-network.io/maitrix-usde/faucet',
        'lvl': 'https://app.x-network.io/maitrix-lvl/faucet'
    }
    
    token_names = {
        'maitrix': 'MAITRIX',
        'usde': 'USDE',
        'lvl': 'LVL'
    }
    
    headers = {
        'authority': 'app.x-network.io',
        'accept': '*/*',
        'content-type': 'application/json',
        'origin': 'https://app.testnet.themaitrix.ai',
        'referer': 'https://app.testnet.themaitrix.ai/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    max_retries = 5
    current_retry = 0
    
    while current_retry < max_retries:
        try:
            proxy = get_random_proxy()
        
            
            response = requests.post(
                endpoints[faucet_type],
                headers=headers,
                json={"address": address},
                proxies=proxy,
                timeout=30
            )
            
            if response.status_code == 429:
                print(Fore.YELLOW + "        💡 Rate limit reached. Sleeping for 10 seconds...")
                time.sleep(10)
                current_retry += 1
                continue
            
            result = response.json()
            
            if result.get('code') == 202:
                remain_time = int(result.get('data', {}).get('remainTime', 0))
                hours = remain_time // 3600
                minutes = (remain_time % 3600) // 60
                print(f"        💡 {Fore.CYAN+Style.BRIGHT}{token_names[faucet_type]}: {Fore.RED + Style.BRIGHT }Already claimed{Fore.RESET}. Wait {hours}h {minutes}m")
                return False
                
            print(Fore.GREEN + f"        ✅ {token_names[faucet_type]} Success")
            print(Fore.CYAN + f"           ↳ Amount: {result.get('data', {}).get('amount')}")
            print(Fore.CYAN + f"           ↳ Tx: {result.get('data', {}).get('txHash')}")
            return True
            
        except requests.exceptions.ProxyError:
            print(Fore.RED + f"        ⚠️ Proxy connection failed, trying another proxy...")
            time.sleep(2)
            current_retry += 1
            
        except requests.exceptions.ConnectionError:
            print(Fore.RED + f"        ⚠️ Connection error, retrying...")
            time.sleep(2)
            current_retry += 1
            
        except requests.exceptions.Timeout:
            print(Fore.RED + f"        ⚠️ Request timeout, retrying...")
            time.sleep(2)
            current_retry += 1
            
        except Exception as e:
            print(Fore.RED + f"        ⚠️ Request failed, retrying...")
            time.sleep(2)
            current_retry += 1
    
    print(Fore.RED + f"        ❌ Failed to claim {token_names[faucet_type]} after {max_retries} attempts")
    return False

def approve_and_mint(private_key):
    try:
        account = Account.from_key(private_key)
        wallet_address = account.address
        
        # print(Fore.GREEN + f"\nProcessing {wallet_address}")
        
        ath_contract = w3.eth.contract(address=ATH_TOKEN, abi=ERC20_ABI)
        ath_balance = ath_contract.functions.balanceOf(wallet_address).call()
        
        if ath_balance < 50000000000000000000:  # 50 ATH
            print(Fore.RED + Style.BRIGHT + "❌ Insufficient ATH balance (need 50 ATH)")
            return False
            
        # Approve
        approve_tx = ath_contract.functions.approve(
            MINT_CONTRACT,
            115792089237316195423570985008687907853269984665640564039457584007913129639935
        ).build_transaction({
            'chainId': w3.eth.chain_id,
            'gas': 50000,
            'maxFeePerGas': w3.to_wei('2.7', 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei('2.5', 'gwei'),
            'nonce': w3.eth.get_transaction_count(wallet_address),
        })
        
        signed_approve = account.sign_transaction(approve_tx)
        approve_hash = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
        print(Fore.YELLOW + "⏳ Waiting for approve confirmation...")
        w3.eth.wait_for_transaction_receipt(approve_hash)
        
        # Mint
        mint_tx = {
            'to': MINT_CONTRACT,
            'data': '0x1bf6318b000000000000000000000000000000000000000000000002b5e3af16b1880000',
            'chainId': w3.eth.chain_id,
            'gas': 205857,
            'maxFeePerGas': w3.to_wei('2.7', 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei('2.5', 'gwei'),
            'nonce': w3.eth.get_transaction_count(wallet_address),
            'value': 0
        }
        
        signed_mint = account.sign_transaction(mint_tx)
        mint_hash = w3.eth.send_raw_transaction(signed_mint.raw_transaction)
        print(Fore.YELLOW + "⏳ Waiting for mint confirmation...")
        receipt = w3.eth.wait_for_transaction_receipt(mint_hash)
        
        if receipt.status == 1:
            print(Fore.GREEN + "✅ Mint successful!")
            return True
        else:
            print(Fore.RED + "❌ Mint failed")
            return False
            
    except Exception as e:
        print(Fore.RED + f"⚠️ Error in mint process: {str(e)}")
        return False

def stake_token(private_key, token_name):
    try:
        account = Account.from_key(private_key)
        token_info = STAKING_CONTRACTS[token_name]
        
        # Get token balance
        token_contract = w3.eth.contract(
            address=Web3.to_checksum_address(token_info['token_address']),
            abi=ERC20_ABI
        )
        balance = token_contract.functions.balanceOf(account.address).call()
        
        if balance <= 0:
            print(Fore.RED + f"❌ No {token_name} balance to stake")
            return False
            
        # Approve
        approve_tx = token_contract.functions.approve(
            token_info['address'],
            balance
        ).build_transaction({
            'chainId': w3.eth.chain_id,
            'gas': 100000,
            'maxFeePerGas': w3.to_wei('2.7', 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei('2.5', 'gwei'),
            'nonce': w3.eth.get_transaction_count(account.address),
        })
        
        signed_approve = account.sign_transaction(approve_tx)
        approve_hash = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
        print(Fore.YELLOW + f"⏳ Waiting for {token_name} approve...")
        w3.eth.wait_for_transaction_receipt(approve_hash)
        
        # Stake
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(token_info['address']),
            abi=STAKING_ABI
        )
        stake_tx = contract.functions.stake(balance).build_transaction({
            'chainId': w3.eth.chain_id,
            'gas': 222110,
            'maxFeePerGas': w3.to_wei('2.7', 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei('2.5', 'gwei'),
            'nonce': w3.eth.get_transaction_count(account.address),
        })
        
        signed_stake = account.sign_transaction(stake_tx)
        stake_hash = w3.eth.send_raw_transaction(signed_stake.raw_transaction)
        print(Fore.YELLOW + f"⏳ Waiting for {token_name} stake...")
        receipt = w3.eth.wait_for_transaction_receipt(stake_hash)
        
        if receipt.status == 1:
            print(Fore.GREEN + f"✅ {token_name} stake successful!")
            return True
        else:
            print(Fore.RED + f"❌ {token_name} stake failed")
            return False
            
    except Exception as e:
        print(Fore.RED + f"⚠️ Error staking {token_name}: {str(e)}")
        return False



def main():
    print_header()
    private_keys = load_private_keys()
    proxies = load_proxies()
    print(Fore.YELLOW + f"Loaded {len(private_keys)} wallet(s) from privatekey.txt")
    print(Fore.YELLOW + f"Loaded {len(proxies)} proxy from proxy.txt\n")
    
    for idx, private_key in enumerate(private_keys, 1):
        account = Account.from_key(private_key)
        print(Style.RESET_ALL+Fore.YELLOW + f"\nProcessing {idx}/{len(private_keys)} {Fore.MAGENTA+Style.BRIGHT}{account.address}{Fore.YELLOW} ===={Fore.RESET}\n")
        
        # 1. Claim Faucets
        print(Fore.CYAN + "💧 Claiming Faucets")
        for faucet in ['maitrix', 'usde', 'lvl']:
            claim_faucet(private_key, faucet, proxies)
            time.sleep(3)
        
        # Wait for faucet tokens
        print(Fore.YELLOW + "⏳ Waiting 3 seconds for faucet tokens appear in your wallet...")
        time.sleep(3)
        
        # 2. Mint AUSD
        print(Fore.CYAN + "💚 Mint AUSD")
        mint_success = approve_and_mint(private_key)
        if mint_success:
            time.sleep(10)
        
        # 3. Stake Tokens
        print(Fore.CYAN + "🔐 Staking Tokens")
        for token in STAKING_CONTRACTS.keys():
            stake_token(private_key, token)
            time.sleep(5)
        
        if idx < len(private_keys):
            print(Fore.YELLOW + "\n⏳ Waiting 3 seconds before next wallet...")
            time.sleep(3)
    
    print(Fore.GREEN + "\n🎉 All operations completed!")

if __name__ == "__main__":
    main() 
