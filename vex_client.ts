import algosdk from "algosdk";
import * as bkr from "beaker-ts";
export class Vex extends bkr.ApplicationClient {
    desc: string = "";
    override appSchema: bkr.Schema = { declared: { ask: { type: bkr.AVMType.uint64, key: "ask", desc: "", static: false }, ask_counter: { type: bkr.AVMType.uint64, key: "ask_book", desc: "", static: false }, asset_a: { type: bkr.AVMType.uint64, key: "asset_a", desc: "", static: false }, asset_b: { type: bkr.AVMType.uint64, key: "asset_b", desc: "", static: false }, bid: { type: bkr.AVMType.uint64, key: "bid", desc: "", static: false }, bid_counter: { type: bkr.AVMType.uint64, key: "bid_book", desc: "", static: false }, max_decimals: { type: bkr.AVMType.uint64, key: "max_decimals", desc: "", static: false }, mid: { type: bkr.AVMType.uint64, key: "mid", desc: "", static: false }, min_lot_a: { type: bkr.AVMType.uint64, key: "min_lot_a", desc: "", static: false }, min_lot_b: { type: bkr.AVMType.uint64, key: "min_lot_b", desc: "", static: false }, seq: { type: bkr.AVMType.uint64, key: "seq", desc: "", static: false } }, dynamic: {} };
    override acctSchema: bkr.Schema = { declared: { avail_bal_a: { type: bkr.AVMType.uint64, key: "avail_bal_a", desc: "", static: false }, avail_bal_b: { type: bkr.AVMType.uint64, key: "avail_bal_b", desc: "", static: false }, orders: { type: bkr.AVMType.bytes, key: "orders", desc: "", static: false }, reserved_bal_a: { type: bkr.AVMType.uint64, key: "reserved_bal_a", desc: "", static: false }, reserved_bal_b: { type: bkr.AVMType.uint64, key: "reserved_bal_b", desc: "", static: false } }, dynamic: {} };
    override approvalProgram: string = "I3ByYWdtYSB2ZXJzaW9uIDgKaW50Y2Jsb2NrIDAgMSAyIDI0IDUwMCAxMDI0CmJ5dGVjYmxvY2sgMHg2MTczNmI1ZjYyNmY2ZjZiIDB4NjI2OTY0NWY2MjZmNmY2YiAweDczNjU3MSAweDA2ODEwMQp0eG4gTnVtQXBwQXJncwppbnRjXzAgLy8gMAo9PQpibnogbWFpbl9sMTIKdHhuYSBBcHBsaWNhdGlvbkFyZ3MgMApwdXNoYnl0ZXMgMHg4ZWM0OTg4MSAvLyAiYm9vc3RyYXAoKXZvaWQiCj09CmJueiBtYWluX2wxMQp0eG5hIEFwcGxpY2F0aW9uQXJncyAwCnB1c2hieXRlcyAweGMxOTg3YTlmIC8vICJjYW5jZWxfb3JkZXIodWludDY0LHVpbnQ2NCx1aW50NjQsdWludDY0KXZvaWQiCj09CmJueiBtYWluX2wxMAp0eG5hIEFwcGxpY2F0aW9uQXJncyAwCnB1c2hieXRlcyAweGJmMTQxZGQ5IC8vICJtb2RpZnlfb3JkZXIodWludDY0LHVpbnQ2NCx1aW50NjQsdWludDY0LHVpbnQ2NCl2b2lkIgo9PQpibnogbWFpbl9sOQp0eG5hIEFwcGxpY2F0aW9uQXJncyAwCnB1c2hieXRlcyAweDA5ZTU3MTE2IC8vICJuZXdfb3JkZXIoYm9vbCx1aW50NjQsdWludDY0KXVpbnQ2NCIKPT0KYm56IG1haW5fbDgKdHhuYSBBcHBsaWNhdGlvbkFyZ3MgMApwdXNoYnl0ZXMgMHg0M2Q3ODIyNiAvLyAicmVnaXN0ZXIoYWNjb3VudCxhc3NldCxhc3NldCl2b2lkIgo9PQpibnogbWFpbl9sNwplcnIKbWFpbl9sNzoKdHhuIE9uQ29tcGxldGlvbgppbnRjXzAgLy8gTm9PcAo9PQp0eG4gQXBwbGljYXRpb25JRAppbnRjXzAgLy8gMAohPQomJgphc3NlcnQKdHhuYSBBcHBsaWNhdGlvbkFyZ3MgMQppbnRjXzAgLy8gMApnZXRieXRlCnN0b3JlIDQ3CnR4bmEgQXBwbGljYXRpb25BcmdzIDIKaW50Y18wIC8vIDAKZ2V0Ynl0ZQpzdG9yZSA0OAp0eG5hIEFwcGxpY2F0aW9uQXJncyAzCmludGNfMCAvLyAwCmdldGJ5dGUKc3RvcmUgNDkKbG9hZCA0Nwpsb2FkIDQ4CmxvYWQgNDkKY2FsbHN1YiByZWdpc3Rlcl8xNQppbnRjXzEgLy8gMQpyZXR1cm4KbWFpbl9sODoKdHhuIE9uQ29tcGxldGlvbgppbnRjXzAgLy8gTm9PcAo9PQp0eG4gQXBwbGljYXRpb25JRAppbnRjXzAgLy8gMAohPQomJgphc3NlcnQKdHhuYSBBcHBsaWNhdGlvbkFyZ3MgMQppbnRjXzAgLy8gMApwdXNoaW50IDggLy8gOAoqCmdldGJpdApzdG9yZSAzOQp0eG5hIEFwcGxpY2F0aW9uQXJncyAyCmJ0b2kKc3RvcmUgNDAKdHhuYSBBcHBsaWNhdGlvbkFyZ3MgMwpidG9pCnN0b3JlIDQxCmxvYWQgMzkKbG9hZCA0MApsb2FkIDQxCmNhbGxzdWIgbmV3b3JkZXJfMTQKc3RvcmUgNDIKcHVzaGJ5dGVzIDB4MTUxZjdjNzUgLy8gMHgxNTFmN2M3NQpsb2FkIDQyCml0b2IKY29uY2F0CmxvZwppbnRjXzEgLy8gMQpyZXR1cm4KbWFpbl9sOToKdHhuIE9uQ29tcGxldGlvbgppbnRjXzAgLy8gTm9PcAo9PQp0eG4gQXBwbGljYXRpb25JRAppbnRjXzAgLy8gMAohPQomJgphc3NlcnQKdHhuYSBBcHBsaWNhdGlvbkFyZ3MgMQpidG9pCnN0b3JlIDM0CnR4bmEgQXBwbGljYXRpb25BcmdzIDIKYnRvaQpzdG9yZSAzNQp0eG5hIEFwcGxpY2F0aW9uQXJncyAzCmJ0b2kKc3RvcmUgMzYKdHhuYSBBcHBsaWNhdGlvbkFyZ3MgNApidG9pCnN0b3JlIDM3CnR4bmEgQXBwbGljYXRpb25BcmdzIDUKYnRvaQpzdG9yZSAzOApsb2FkIDM0CmxvYWQgMzUKbG9hZCAzNgpsb2FkIDM3CmxvYWQgMzgKY2FsbHN1YiBtb2RpZnlvcmRlcl8xMwppbnRjXzEgLy8gMQpyZXR1cm4KbWFpbl9sMTA6CnR4biBPbkNvbXBsZXRpb24KaW50Y18wIC8vIE5vT3AKPT0KdHhuIEFwcGxpY2F0aW9uSUQKaW50Y18wIC8vIDAKIT0KJiYKYXNzZXJ0CnR4bmEgQXBwbGljYXRpb25BcmdzIDEKYnRvaQpzdG9yZSAzMAp0eG5hIEFwcGxpY2F0aW9uQXJncyAyCmJ0b2kKc3RvcmUgMzEKdHhuYSBBcHBsaWNhdGlvbkFyZ3MgMwpidG9pCnN0b3JlIDMyCnR4bmEgQXBwbGljYXRpb25BcmdzIDQKYnRvaQpzdG9yZSAzMwpsb2FkIDMwCmxvYWQgMzEKbG9hZCAzMgpsb2FkIDMzCmNhbGxzdWIgY2FuY2Vsb3JkZXJfMTAKaW50Y18xIC8vIDEKcmV0dXJuCm1haW5fbDExOgp0eG4gT25Db21wbGV0aW9uCmludGNfMCAvLyBOb09wCj09CnR4biBBcHBsaWNhdGlvbklECmludGNfMCAvLyAwCiE9CiYmCmFzc2VydApjYWxsc3ViIGJvb3N0cmFwXzkKaW50Y18xIC8vIDEKcmV0dXJuCm1haW5fbDEyOgp0eG4gT25Db21wbGV0aW9uCmludGNfMCAvLyBOb09wCj09CmJueiBtYWluX2wxNAplcnIKbWFpbl9sMTQ6CnR4biBBcHBsaWNhdGlvbklECmludGNfMCAvLyAwCj09CmFzc2VydApjYWxsc3ViIGNyZWF0ZV8wCmludGNfMSAvLyAxCnJldHVybgoKLy8gY3JlYXRlCmNyZWF0ZV8wOgppbnRjXzEgLy8gMQpyZXR1cm4KCi8vIHVuc29ydGVkCnVuc29ydGVkXzE6CnN0b3JlIDExCnN0b3JlIDEwCnN0b3JlIDkKbG9hZCA5CmxlbgppbnRjXzAgLy8gMAo9PQpsb2FkIDEwCmxlbgppbnRjXzAgLy8gMAo9PQp8fApibnogdW5zb3J0ZWRfMV9sNApsb2FkIDExCmJueiB1bnNvcnRlZF8xX2wzCmxvYWQgOQpleHRyYWN0IDAgOApsb2FkIDkKZXh0cmFjdCA4IDgKYn4KY29uY2F0CmxvYWQgMTAKZXh0cmFjdCAwIDgKbG9hZCAxMApleHRyYWN0IDggOApifgpjb25jYXQKYj4KYiB1bnNvcnRlZF8xX2w1CnVuc29ydGVkXzFfbDM6CmxvYWQgOQpleHRyYWN0IDAgMTYKbG9hZCAxMApleHRyYWN0IDAgMTYKYjwKYiB1bnNvcnRlZF8xX2w1CnVuc29ydGVkXzFfbDQ6CmludGNfMCAvLyAwCnVuc29ydGVkXzFfbDU6CnJldHN1YgoKLy8gcHFfaW5zZXJ0CnBxaW5zZXJ0XzI6CnN0b3JlIDIKc3RvcmUgMQpzdG9yZSAwCmxvYWQgMApsb2FkIDAKYXBwX2dsb2JhbF9nZXQKbG9hZCAxCmxlbgoqCmxvYWQgMQpib3hfcmVwbGFjZQpsb2FkIDAKbG9hZCAwCmFwcF9nbG9iYWxfZ2V0CmxvYWQgMQpsZW4KbG9hZCAyCmNhbGxzdWIgcHF1cGhlYXBfNQpsb2FkIDAKbG9hZCAwCmFwcF9nbG9iYWxfZ2V0CmludGNfMSAvLyAxCisKYXBwX2dsb2JhbF9wdXQKcmV0c3ViCgovLyBwcV9yZW1vdmUKcHFyZW1vdmVfMzoKc3RvcmUgMjEKc3RvcmUgMjAKc3RvcmUgMTkKc3RvcmUgMTgKbG9hZCAxOApsb2FkIDE4CmFwcF9nbG9iYWxfZ2V0CmludGNfMSAvLyAxCi0KYXBwX2dsb2JhbF9wdXQKbG9hZCAxOApsb2FkIDE5CmxvYWQgMTgKYXBwX2dsb2JhbF9nZXQKbG9hZCAyMApjYWxsc3ViIHBxc3dhcF80CmxvYWQgMTgKbG9hZCAxOQpsb2FkIDIwCmxvYWQgMjEKY2FsbHN1YiBwcWRvd25oZWFwXzYKbG9hZCAxOApsb2FkIDE4CmFwcF9nbG9iYWxfZ2V0CmxvYWQgMjAKYnplcm8KbGVuCioKbG9hZCAyMApiemVybwpib3hfcmVwbGFjZQpyZXRzdWIKCi8vIHBxX3N3YXAKcHFzd2FwXzQ6CnN0b3JlIDE1CnN0b3JlIDE0CnN0b3JlIDEzCnN0b3JlIDEyCmxvYWQgMTIKbG9hZCAxMwpsb2FkIDE1CioKbG9hZCAxNQpib3hfZXh0cmFjdApzdG9yZSAxNgpsb2FkIDEyCmxvYWQgMTQKbG9hZCAxNQoqCmxvYWQgMTUKYm94X2V4dHJhY3QKc3RvcmUgMTcKbG9hZCAxMgpsb2FkIDE0CmxvYWQgMTYKbGVuCioKbG9hZCAxNgpib3hfcmVwbGFjZQpsb2FkIDEyCmxvYWQgMTMKbG9hZCAxNwpsZW4KKgpsb2FkIDE3CmJveF9yZXBsYWNlCnJldHN1YgoKLy8gcHFfdXBoZWFwCnBxdXBoZWFwXzU6CnN0b3JlIDYKc3RvcmUgNQpzdG9yZSA0CnN0b3JlIDMKbG9hZCA0CmludGNfMCAvLyAwCiE9CmJ6IHBxdXBoZWFwXzVfbDkKaW50YyA0IC8vIDUwMApwdXNoaW50IDEwIC8vIDEwCisKc3RvcmUgNwpwcXVwaGVhcF81X2wyOgpsb2FkIDcKZ2xvYmFsIE9wY29kZUJ1ZGdldAo+CmJueiBwcXVwaGVhcF81X2w4CmxvYWQgNAppbnRjXzIgLy8gMgolCmludGNfMCAvLyAwCj09CmJueiBwcXVwaGVhcF81X2w3CmxvYWQgNAppbnRjXzEgLy8gMQotCnBxdXBoZWFwXzVfbDU6CmludGNfMiAvLyAyCi8Kc3RvcmUgOApsb2FkIDMKbG9hZCA0CmxvYWQgNQoqCmxvYWQgNQpib3hfZXh0cmFjdApsb2FkIDMKbG9hZCA4CmxvYWQgNQoqCmxvYWQgNQpib3hfZXh0cmFjdApsb2FkIDYKY2FsbHN1YiB1bnNvcnRlZF8xCmJ6IHBxdXBoZWFwXzVfbDkKbG9hZCAzCmxvYWQgNApsb2FkIDgKbG9hZCA1CmNhbGxzdWIgcHFzd2FwXzQKbG9hZCAzCmxvYWQgOApsb2FkIDUKbG9hZCA2CmxvYWQgMwpsb2FkIDQKbG9hZCA1CmxvYWQgNgpsb2FkIDcKbG9hZCA4CnVuY292ZXIgOQp1bmNvdmVyIDkKdW5jb3ZlciA5CnVuY292ZXIgOQpjYWxsc3ViIHBxdXBoZWFwXzUKc3RvcmUgOApzdG9yZSA3CnN0b3JlIDYKc3RvcmUgNQpzdG9yZSA0CnN0b3JlIDMKYiBwcXVwaGVhcF81X2w5CnBxdXBoZWFwXzVfbDc6CmxvYWQgNAppbnRjXzIgLy8gMgotCmIgcHF1cGhlYXBfNV9sNQpwcXVwaGVhcF81X2w4OgppdHhuX2JlZ2luCnB1c2hpbnQgNiAvLyBhcHBsCml0eG5fZmllbGQgVHlwZUVudW0KcHVzaGludCA1IC8vIERlbGV0ZUFwcGxpY2F0aW9uCml0eG5fZmllbGQgT25Db21wbGV0aW9uCmJ5dGVjXzMgLy8gMHgwNjgxMDEKaXR4bl9maWVsZCBBcHByb3ZhbFByb2dyYW0KYnl0ZWNfMyAvLyAweDA2ODEwMQppdHhuX2ZpZWxkIENsZWFyU3RhdGVQcm9ncmFtCml0eG5fc3VibWl0CmIgcHF1cGhlYXBfNV9sMgpwcXVwaGVhcF81X2w5OgpyZXRzdWIKCi8vIHBxX2Rvd25oZWFwCnBxZG93bmhlYXBfNjoKc3RvcmUgMjUKc3RvcmUgMjQKc3RvcmUgMjMKc3RvcmUgMjIKbG9hZCAyMwpsb2FkIDIyCmFwcF9nbG9iYWxfZ2V0CjwKYnogcHFkb3duaGVhcF82X2wxMgppbnRjIDQgLy8gNTAwCnB1c2hpbnQgMTAgLy8gMTAKKwpzdG9yZSAyNgpwcWRvd25oZWFwXzZfbDI6CmxvYWQgMjYKZ2xvYmFsIE9wY29kZUJ1ZGdldAo+CmJueiBwcWRvd25oZWFwXzZfbDExCmxvYWQgMjMKc3RvcmUgMjcKbG9hZCAyMwppbnRjXzIgLy8gMgoqCmludGNfMSAvLyAxCisKc3RvcmUgMjgKbG9hZCAyMwppbnRjXzIgLy8gMgoqCmludGNfMiAvLyAyCisKc3RvcmUgMjkKbG9hZCAyOApsb2FkIDIyCmFwcF9nbG9iYWxfZ2V0CjwKYm56IHBxZG93bmhlYXBfNl9sOQpwcWRvd25oZWFwXzZfbDQ6CmxvYWQgMjkKbG9hZCAyMgphcHBfZ2xvYmFsX2dldAo8CmJueiBwcWRvd25oZWFwXzZfbDcKcHFkb3duaGVhcF82X2w1Ogpsb2FkIDI3CmxvYWQgMjMKIT0KYnogcHFkb3duaGVhcF82X2wxMgpsb2FkIDIyCmxvYWQgMjMKbG9hZCAyNwpsb2FkIDI0CmNhbGxzdWIgcHFzd2FwXzQKbG9hZCAyMgpsb2FkIDI3CmxvYWQgMjQKbG9hZCAyNQpsb2FkIDIyCmxvYWQgMjMKbG9hZCAyNApsb2FkIDI1CmxvYWQgMjYKbG9hZCAyNwpsb2FkIDI4CmxvYWQgMjkKdW5jb3ZlciAxMQp1bmNvdmVyIDExCnVuY292ZXIgMTEKdW5jb3ZlciAxMQpjYWxsc3ViIHBxZG93bmhlYXBfNgpzdG9yZSAyOQpzdG9yZSAyOApzdG9yZSAyNwpzdG9yZSAyNgpzdG9yZSAyNQpzdG9yZSAyNApzdG9yZSAyMwpzdG9yZSAyMgpiIHBxZG93bmhlYXBfNl9sMTIKcHFkb3duaGVhcF82X2w3Ogpsb2FkIDIyCmxvYWQgMjkKbG9hZCAyNAoqCmxvYWQgMjQKYm94X2V4dHJhY3QKbG9hZCAyMgpsb2FkIDI3CmxvYWQgMjQKKgpsb2FkIDI0CmJveF9leHRyYWN0CmxvYWQgMjUKY2FsbHN1YiB1bnNvcnRlZF8xCmJ6IHBxZG93bmhlYXBfNl9sNQpsb2FkIDI5CnN0b3JlIDI3CmIgcHFkb3duaGVhcF82X2w1CnBxZG93bmhlYXBfNl9sOToKbG9hZCAyMgpsb2FkIDI4CmxvYWQgMjQKKgpsb2FkIDI0CmJveF9leHRyYWN0CmxvYWQgMjIKbG9hZCAyNwpsb2FkIDI0CioKbG9hZCAyNApib3hfZXh0cmFjdApsb2FkIDI1CmNhbGxzdWIgdW5zb3J0ZWRfMQpieiBwcWRvd25oZWFwXzZfbDQKbG9hZCAyOApzdG9yZSAyNwpiIHBxZG93bmhlYXBfNl9sNApwcWRvd25oZWFwXzZfbDExOgppdHhuX2JlZ2luCnB1c2hpbnQgNiAvLyBhcHBsCml0eG5fZmllbGQgVHlwZUVudW0KcHVzaGludCA1IC8vIERlbGV0ZUFwcGxpY2F0aW9uCml0eG5fZmllbGQgT25Db21wbGV0aW9uCmJ5dGVjXzMgLy8gMHgwNjgxMDEKaXR4bl9maWVsZCBBcHByb3ZhbFByb2dyYW0KYnl0ZWNfMyAvLyAweDA2ODEwMQppdHhuX2ZpZWxkIENsZWFyU3RhdGVQcm9ncmFtCml0eG5fc3VibWl0CmIgcHFkb3duaGVhcF82X2wyCnBxZG93bmhlYXBfNl9sMTI6CnJldHN1YgoKLy8gYWRkX2FzawphZGRhc2tfNzoKc3RvcmUgNjEKc3RvcmUgNjAKc3RvcmUgNTkKbG9hZCA2MQpzdG9yZSA2Mgpsb2FkIDU5Cml0b2IKbG9hZCA2MgppdG9iCmNvbmNhdApsb2FkIDYwCml0b2IKY29uY2F0CnN0b3JlIDYzCmJ5dGVjXzAgLy8gImFza19ib29rIgpsb2FkIDYzCmludGNfMSAvLyAxCmNhbGxzdWIgcHFpbnNlcnRfMgpyZXRzdWIKCi8vIGFkZF9iaWQKYWRkYmlkXzg6CnN0b3JlIDY2CnN0b3JlIDY1CnN0b3JlIDY0CmxvYWQgNjYKc3RvcmUgNjcKbG9hZCA2NAppdG9iCmxvYWQgNjcKaXRvYgpjb25jYXQKbG9hZCA2NQppdG9iCmNvbmNhdApzdG9yZSA2OApieXRlY18xIC8vICJiaWRfYm9vayIKbG9hZCA2OAppbnRjXzAgLy8gMApjYWxsc3ViIHBxaW5zZXJ0XzIKcmV0c3ViCgovLyBib29zdHJhcApib29zdHJhcF85OgpieXRlY18wIC8vICJhc2tfYm9vayIKaW50YyA1IC8vIDEwMjQKYm94X2NyZWF0ZQphc3NlcnQKYnl0ZWNfMSAvLyAiYmlkX2Jvb2siCmludGMgNSAvLyAxMDI0CmJveF9jcmVhdGUKYXNzZXJ0CnJldHN1YgoKLy8gY2FuY2VsX29yZGVyCmNhbmNlbG9yZGVyXzEwOgpzdG9yZSA1MwpzdG9yZSA1MgpzdG9yZSA1MQpzdG9yZSA1MAppbnRjXzAgLy8gMAphc3NlcnQKcmV0c3ViCgovLyBmaWxsX2Fza3MKZmlsbGFza3NfMTE6CnN0b3JlIDcwCnN0b3JlIDY5CmJ5dGVjXzAgLy8gImFza19ib29rIgphcHBfZ2xvYmFsX2dldAppbnRjXzAgLy8gMAo9PQpsb2FkIDcwCmludGNfMCAvLyAwCj09Cnx8CmJueiBmaWxsYXNrc18xMV9sNgpieXRlY18wIC8vICJhc2tfYm9vayIKaW50Y18wIC8vIDAKaW50Y18zIC8vIDI0CioKaW50Y18zIC8vIDI0CmJveF9leHRyYWN0CnN0b3JlIDcxCmxvYWQgNzEKaW50Y18wIC8vIDAKZXh0cmFjdF91aW50NjQKc3RvcmUgNzIKbG9hZCA3MQpwdXNoaW50IDE2IC8vIDE2CmV4dHJhY3RfdWludDY0CnN0b3JlIDczCmxvYWQgNzIKbG9hZCA2OQo+CmJueiBmaWxsYXNrc18xMV9sNQpsb2FkIDczCmxvYWQgNzAKPD0KYm56IGZpbGxhc2tzXzExX2w0CmxvYWQgNzEKcHVzaGludCA4IC8vIDgKZXh0cmFjdF91aW50NjQKc3RvcmUgNzQKbG9hZCA3Mwpsb2FkIDcwCi0Kc3RvcmUgNzUKbG9hZCA3MgppdG9iCmxvYWQgNzQKaXRvYgpjb25jYXQKbG9hZCA3NQppdG9iCmNvbmNhdApzdG9yZSA3MQpieXRlY18wIC8vICJhc2tfYm9vayIKaW50Y18wIC8vIDAKbG9hZCA3MQpsZW4KKgpsb2FkIDcxCmJveF9yZXBsYWNlCmludGNfMCAvLyAwCmIgZmlsbGFza3NfMTFfbDcKZmlsbGFza3NfMTFfbDQ6CmJ5dGVjXzAgLy8gImFza19ib29rIgppbnRjXzAgLy8gMAppbnRjXzMgLy8gMjQKaW50Y18xIC8vIDEKY2FsbHN1YiBwcXJlbW92ZV8zCmxvYWQgNjkKbG9hZCA3MApsb2FkIDczCi0KbG9hZCA2OQpsb2FkIDcwCmxvYWQgNzEKbG9hZCA3Mgpsb2FkIDczCmxvYWQgNzQKbG9hZCA3NQp1bmNvdmVyIDgKdW5jb3ZlciA4CmNhbGxzdWIgZmlsbGFza3NfMTEKY292ZXIgNwpzdG9yZSA3NQpzdG9yZSA3NApzdG9yZSA3MwpzdG9yZSA3MgpzdG9yZSA3MQpzdG9yZSA3MApzdG9yZSA2OQpiIGZpbGxhc2tzXzExX2w3CmZpbGxhc2tzXzExX2w1Ogpsb2FkIDcwCnJldHN1YgpmaWxsYXNrc18xMV9sNjoKbG9hZCA3MApyZXRzdWIKZmlsbGFza3NfMTFfbDc6CnJldHN1YgoKLy8gZmlsbF9iaWRzCmZpbGxiaWRzXzEyOgpzdG9yZSA3NwpzdG9yZSA3NgpieXRlY18xIC8vICJiaWRfYm9vayIKYXBwX2dsb2JhbF9nZXQKaW50Y18wIC8vIDAKPT0KbG9hZCA3NwppbnRjXzAgLy8gMAo9PQp8fApibnogZmlsbGJpZHNfMTJfbDYKYnl0ZWNfMSAvLyAiYmlkX2Jvb2siCmludGNfMCAvLyAwCmludGNfMyAvLyAyNAoqCmludGNfMyAvLyAyNApib3hfZXh0cmFjdApzdG9yZSA3OApsb2FkIDc4CmludGNfMCAvLyAwCmV4dHJhY3RfdWludDY0CnN0b3JlIDc5CmxvYWQgNzgKcHVzaGludCAxNiAvLyAxNgpleHRyYWN0X3VpbnQ2NApzdG9yZSA4MApsb2FkIDc5CmxvYWQgNzYKPApibnogZmlsbGJpZHNfMTJfbDUKbG9hZCA4MApsb2FkIDc3Cjw9CmJueiBmaWxsYmlkc18xMl9sNApsb2FkIDc4CnB1c2hpbnQgOCAvLyA4CmV4dHJhY3RfdWludDY0CnN0b3JlIDgxCmxvYWQgODAKbG9hZCA3NwotCnN0b3JlIDgyCmxvYWQgNzkKaXRvYgpsb2FkIDgxCml0b2IKY29uY2F0CmxvYWQgODIKaXRvYgpjb25jYXQKc3RvcmUgNzgKYnl0ZWNfMSAvLyAiYmlkX2Jvb2siCmludGNfMCAvLyAwCmxvYWQgNzgKbGVuCioKbG9hZCA3OApib3hfcmVwbGFjZQppbnRjXzAgLy8gMApiIGZpbGxiaWRzXzEyX2w3CmZpbGxiaWRzXzEyX2w0OgpieXRlY18xIC8vICJiaWRfYm9vayIKaW50Y18wIC8vIDAKaW50Y18zIC8vIDI0CmludGNfMCAvLyAwCmNhbGxzdWIgcHFyZW1vdmVfMwpsb2FkIDc2CmxvYWQgNzcKbG9hZCA4MAotCmxvYWQgNzYKbG9hZCA3Nwpsb2FkIDc4CmxvYWQgNzkKbG9hZCA4MApsb2FkIDgxCmxvYWQgODIKdW5jb3ZlciA4CnVuY292ZXIgOApjYWxsc3ViIGZpbGxiaWRzXzEyCmNvdmVyIDcKc3RvcmUgODIKc3RvcmUgODEKc3RvcmUgODAKc3RvcmUgNzkKc3RvcmUgNzgKc3RvcmUgNzcKc3RvcmUgNzYKYiBmaWxsYmlkc18xMl9sNwpmaWxsYmlkc18xMl9sNToKbG9hZCA3NwpyZXRzdWIKZmlsbGJpZHNfMTJfbDY6CmxvYWQgNzcKcmV0c3ViCmZpbGxiaWRzXzEyX2w3OgpyZXRzdWIKCi8vIG1vZGlmeV9vcmRlcgptb2RpZnlvcmRlcl8xMzoKc3RvcmUgNTgKc3RvcmUgNTcKc3RvcmUgNTYKc3RvcmUgNTUKc3RvcmUgNTQKaW50Y18wIC8vIDAKYXNzZXJ0CnJldHN1YgoKLy8gbmV3X29yZGVyCm5ld29yZGVyXzE0OgpzdG9yZSA0NQpzdG9yZSA0NApzdG9yZSA0Mwpsb2FkIDQ1CnN0b3JlIDQ2CmxvYWQgNDMKYm56IG5ld29yZGVyXzE0X2wzCmxvYWQgNDQKbG9hZCA0NQpjYWxsc3ViIGZpbGxiaWRzXzEyCnN0b3JlIDQ1CmxvYWQgNDUKYnogbmV3b3JkZXJfMTRfbDUKbG9hZCA0NApsb2FkIDQ1CmJ5dGVjXzIgLy8gInNlcSIKYnl0ZWNfMiAvLyAic2VxIgphcHBfZ2xvYmFsX2dldAppbnRjXzEgLy8gMQorCmFwcF9nbG9iYWxfcHV0CmJ5dGVjXzIgLy8gInNlcSIKYXBwX2dsb2JhbF9nZXQKY2FsbHN1YiBhZGRhc2tfNwpiIG5ld29yZGVyXzE0X2w1Cm5ld29yZGVyXzE0X2wzOgpsb2FkIDQ0CmxvYWQgNDUKY2FsbHN1YiBmaWxsYXNrc18xMQpzdG9yZSA0NQpsb2FkIDQ1CmJ6IG5ld29yZGVyXzE0X2w1CmxvYWQgNDQKbG9hZCA0NQpieXRlY18yIC8vICJzZXEiCmJ5dGVjXzIgLy8gInNlcSIKYXBwX2dsb2JhbF9nZXQKaW50Y18xIC8vIDEKKwphcHBfZ2xvYmFsX3B1dApieXRlY18yIC8vICJzZXEiCmFwcF9nbG9iYWxfZ2V0CmNhbGxzdWIgYWRkYmlkXzgKbmV3b3JkZXJfMTRfbDU6CmxvYWQgNDYKbG9hZCA0NQotCnN0b3JlIDQ2CmxvYWQgNDYKcmV0c3ViCgovLyByZWdpc3RlcgpyZWdpc3Rlcl8xNToKc3RvcmUgODUKc3RvcmUgODQKc3RvcmUgODMKaW50Y18wIC8vIDAKYXNzZXJ0CnJldHN1Yg==";
    override clearProgram: string = "I3ByYWdtYSB2ZXJzaW9uIDgKcHVzaGludCAwIC8vIDAKcmV0dXJu";
    methods: algosdk.ABIMethod[] = [
        new algosdk.ABIMethod({ name: "boostrap", desc: "", args: [], returns: { type: "void", desc: "" } }),
        new algosdk.ABIMethod({ name: "cancel_order", desc: "", args: [{ type: "uint64", name: "price", desc: "" }, { type: "uint64", name: "seq", desc: "" }, { type: "uint64", name: "size", desc: "" }, { type: "uint64", name: "acct_id", desc: "" }], returns: { type: "void", desc: "" } }),
        new algosdk.ABIMethod({ name: "modify_order", desc: "", args: [{ type: "uint64", name: "price", desc: "" }, { type: "uint64", name: "seq", desc: "" }, { type: "uint64", name: "size", desc: "" }, { type: "uint64", name: "acct_id", desc: "" }, { type: "uint64", name: "new_size", desc: "" }], returns: { type: "void", desc: "" } }),
        new algosdk.ABIMethod({ name: "new_order", desc: "", args: [{ type: "bool", name: "is_bid", desc: "" }, { type: "uint64", name: "price", desc: "" }, { type: "uint64", name: "size", desc: "" }], returns: { type: "uint64", desc: "" } }),
        new algosdk.ABIMethod({ name: "register", desc: "", args: [{ type: "account", name: "acct", desc: "" }, { type: "asset", name: "asset_a", desc: "" }, { type: "asset", name: "asset_b", desc: "" }], returns: { type: "void", desc: "" } })
    ];
    async boostrap(txnParams?: bkr.TransactionOverrides): Promise<bkr.ABIResult<void>> {
        const result = await this.call(algosdk.getMethodByName(this.methods, "boostrap"), {}, txnParams);
        return new bkr.ABIResult<void>(result);
    }
    async cancel_order(args: {
        price: bigint;
        seq: bigint;
        size: bigint;
        acct_id: bigint;
    }, txnParams?: bkr.TransactionOverrides): Promise<bkr.ABIResult<void>> {
        const result = await this.call(algosdk.getMethodByName(this.methods, "cancel_order"), { price: args.price, seq: args.seq, size: args.size, acct_id: args.acct_id }, txnParams);
        return new bkr.ABIResult<void>(result);
    }
    async modify_order(args: {
        price: bigint;
        seq: bigint;
        size: bigint;
        acct_id: bigint;
        new_size: bigint;
    }, txnParams?: bkr.TransactionOverrides): Promise<bkr.ABIResult<void>> {
        const result = await this.call(algosdk.getMethodByName(this.methods, "modify_order"), { price: args.price, seq: args.seq, size: args.size, acct_id: args.acct_id, new_size: args.new_size }, txnParams);
        return new bkr.ABIResult<void>(result);
    }
    async new_order(args: {
        is_bid: boolean;
        price: bigint;
        size: bigint;
    }, txnParams?: bkr.TransactionOverrides): Promise<bkr.ABIResult<bigint>> {
        const result = await this.call(algosdk.getMethodByName(this.methods, "new_order"), { is_bid: args.is_bid, price: args.price, size: args.size }, txnParams);
        return new bkr.ABIResult<bigint>(result, result.returnValue as bigint);
    }
    async register(args: {
        acct: string;
        asset_a: bigint;
        asset_b: bigint;
    }, txnParams?: bkr.TransactionOverrides): Promise<bkr.ABIResult<void>> {
        const result = await this.call(algosdk.getMethodByName(this.methods, "register"), { acct: args.acct, asset_a: args.asset_a, asset_b: args.asset_b }, txnParams);
        return new bkr.ABIResult<void>(result);
    }
}