async def run(nre):
  accounts = await nre.get_accounts(predeployed=True)
  account = accounts[0]
  tx = await account.declare("Account", nile_account=True)
  await tx.execute()