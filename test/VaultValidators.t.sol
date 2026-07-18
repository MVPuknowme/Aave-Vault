// SPDX-License-Identifier: MIT

pragma solidity ^0.8.10;

import "forge-std/Test.sol";
import {VaultValidators} from "../src/libraries/VaultValidators.sol";

contract VaultValidatorsHarness {
    function validate(
        address owner,
        uint256 initialLockDeposit,
        string memory shareName,
        string memory shareSymbol
    ) external pure {
        VaultValidators.validateInitParams(
            owner,
            initialLockDeposit,
            shareName,
            shareSymbol
        );
    }
}

contract VaultValidatorsTest is Test {
    VaultValidatorsHarness internal harness;

    function setUp() public {
        harness = new VaultValidatorsHarness();
    }

    function testValidateInitParamsAcceptsValidValues() public view {
        harness.validate(address(0xBEEF), 1, "Aave Vault", "aVault");
    }

    function testValidateInitParamsRejectsZeroOwner() public {
        vm.expectRevert("ZERO_ADDRESS_NOT_VALID");
        harness.validate(address(0), 1, "Aave Vault", "aVault");
    }

    function testValidateInitParamsRejectsZeroDeposit() public {
        vm.expectRevert("ZERO_INITIAL_LOCK_DEPOSIT");
        harness.validate(address(0xBEEF), 0, "Aave Vault", "aVault");
    }

    function testValidateInitParamsRejectsEmptyName() public {
        vm.expectRevert("EMPTY_SHARE_NAME");
        harness.validate(address(0xBEEF), 1, "", "aVault");
    }

    function testValidateInitParamsRejectsEmptySymbol() public {
        vm.expectRevert("EMPTY_SHARE_SYMBOL");
        harness.validate(address(0xBEEF), 1, "Aave Vault", "");
    }
}
