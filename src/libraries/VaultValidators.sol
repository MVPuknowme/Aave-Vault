// SPDX-License-Identifier: UNLICENSED
// All Rights Reserved © AaveCo

pragma solidity ^0.8.10;

/**
 * @title VaultValidators
 * @author Aave Labs
 * @notice Helper library for validating common vault parameters.
 */
library VaultValidators {
    /**
     * @dev Validate initialization parameters shared across vault implementations.
     */
    function validateInitParams(
        address owner,
        uint256 initialLockDeposit,
        string memory shareName,
        string memory shareSymbol
    ) internal pure {
        require(owner != address(0), "ZERO_ADDRESS_NOT_VALID");
        require(initialLockDeposit != 0, "ZERO_INITIAL_LOCK_DEPOSIT");
        require(bytes(shareName).length > 0, "EMPTY_SHARE_NAME");
        require(bytes(shareSymbol).length > 0, "EMPTY_SHARE_SYMBOL");
    }
}
