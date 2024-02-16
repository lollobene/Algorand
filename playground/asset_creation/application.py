import beaker
import pyteal as pt

app = beaker.Application("AssetCreation")


@app.external
def create_asset(v: pt.abi.String, *, output: pt.abi.String) -> pt.Expr:
    return pt.Seq(
        pt.InnerTxnBuilder.Execute(
            {
                pt.TxnField.fee: pt.Int(0),
                pt.TxnField.type_enum: pt.TxnType.AssetConfig,
                pt.TxnField.config_asset_total: pt.Int(1000),
                pt.TxnField.config_asset_decimals:  pt.Int(1),
                pt.TxnField.config_asset_default_frozen:  pt.Int(1),
                pt.TxnField.config_asset_unit_name: pt.Bytes("ASSET"),
                pt.TxnField.config_asset_name: pt.Bytes("ASSET_NAME")
            }
        ),

    )
