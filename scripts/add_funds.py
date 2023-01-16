from nile.common import ETH_TOKEN_ADDRESS

async def run(nre):
    accounts = await nre.get_accounts(predeployed=True)
    account = accounts[0]
    recipient = "0x04d3f77f305c02d158f159a91e00f4562e8697b7025559aa5f0497446c3bd5de"

    amount = [2 * 10 ** 18, 0]
    print(f"transferring {amount} to {recipient} from {accounts[0].address}")
    tx = await account.send(ETH_TOKEN_ADDRESS, "transfer", [recipient, *amount])
    await tx.execute()

    # eth
    recipient = "0x07633f2234e6a3e71c92a757c86517953affb066cffdef1d560fbfb9036f3aa3"

    print(f"transferring {amount} to {recipient} from {accounts[0].address}")
    tx = await account.send(ETH_TOKEN_ADDRESS, "transfer", [recipient, *amount])
    await tx.execute()