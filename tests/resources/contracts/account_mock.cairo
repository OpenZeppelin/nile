%lang starknet

# The StarkNet compiler checks for an external "__execute__" method
# if found, it expects an "--account_contract" flag during compilation
@external
func __execute__():
    return ()
end
