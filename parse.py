import gzip
import xml.etree.ElementTree as ET


def load_gzipped(filepath):
    with gzip.open(filepath) as file_:
        return ET.parse(file_).getroot()


def load_mjlog(filepath):
    if not filepath.endswith('.gz'):
        try:
            return ET.parse(filepath).getroot()
        except:
            pass
    return load_gzipped(filepath)
    

def ensure_unicode(string):
    """Convert string into unicode."""
    if not isinstance(string, str):
        return string.decode('utf-8')
    return string

def ensure_str(string):
    """Convert string into str (bytes) object."""
    if not isinstance(string, str):
        return string.decode('utf-8')
    return string


from urllib.parse import unquote as _unquote
def unquote(string):
    return _unquote(string)


def _parse_str_list(val, type_):
    return [type_(val) for val in val.split(',')] if val else []


###############################################################################
def _parse_shuffle(attrib):
    return {
        'seed': attrib['seed'],
        'ref': attrib['ref'],
    }


###############################################################################
def _parse_game_config(game_config):
    test = not bool(game_config & 0x01)
    tokujou = bool((game_config & 0x20) >> 5)
    joukyu = bool((game_config & 0x80) >> 7)
    if tokujou and joukyu:
        table = 'tenhou'
    elif test:
        table = 'test'
    elif tokujou:
        table = 'tokujou'
    elif joukyu:
        table = 'joukyu'
    else:
        table = 'dan-i'
    config = {
        'red': not bool((game_config & 0x02) >> 1),
        'kui': not bool((game_config & 0x04) >> 2),
        'ton-nan': bool((game_config & 0x08) >> 3),
        'sanma': bool((game_config & 0x10) >> 4),
        'soku': bool((game_config & 0x40) >> 6),
    }
    return table, config


def _parse_go(attrib):
    table, config = _parse_game_config(int(attrib['type']))
    number_ = int(attrib['lobby']) if 'lobby' in attrib else None
    return {'table': table, 'config': config, 'lobby': number_}


###############################################################################
def _parse_resume(attrib):
    index = int(list(attrib.keys())[0][1])
    name = unquote(list(attrib.values())[0])
    return {'index': index, 'name': name}


def _parse_un(attrib):
    keys = ['n0', 'n1', 'n2', 'n3']
    names = [unquote(attrib[key]) for key in keys if key in attrib]
    dans = _parse_str_list(attrib.get('dan', '-1,-1,-1,-1'), type_=int)
    rates = _parse_str_list(attrib['rate'], type_=float)
    sexes = _parse_str_list(attrib['sx'], type_=ensure_unicode)
    return [
        {'name': name, 'dan': dan, 'rate': rate, 'sex': sex}
        for name, dan, rate, sex in zip(names, dans, rates, sexes)
    ]


################################################################################
def _parse_taikyoku(attrib):
    return {'oya': attrib['oya']}


###############################################################################
def _parse_score(data):
    return [score * 100 for score in _parse_str_list(data, type_=int)]


def _parse_init(attrib):
    seed = _parse_str_list(attrib['seed'], type_=int)
    scores = _parse_score(attrib['ten'])
    hands = [
        _parse_str_list(attrib[key], type_=int)
        for key in ['hai0', 'hai1', 'hai2', 'hai3'] if key in attrib
    ]
    return {
        'oya': attrib['oya'],
        'scores': scores,
        'hands': hands,
        'round': seed[0],
        'combo': seed[1],
        'reach': seed[2],
        'dices': seed[3:5],
        'dora': seed[5],
    }


###############################################################################
def _parse_draw(tag):
    player = ord(tag[0]) - ord('T')
    tile = int(tag[1:])
    return {'player': player, 'tile': tile}


###############################################################################
def _parse_discard(tag):
    player = ord(tag[0]) - ord('D')
    tile = int(tag[1:])
    return {'player': player, 'tile': tile}


###############################################################################
def _parse_shuntsu(meld):
    # Adopted from http://tenhou.net/img/tehai.js
    t = (meld & 0xfc00) >> 10
    r = t % 3
    t = t // 3
    t = 9 * (t // 7) + (t % 7)
    t *= 4
    h = [
        t + 4*0 + ((meld & 0x0018)>>3),
        t + 4*1 + ((meld & 0x0060)>>5),
        t + 4*2 + ((meld & 0x0180)>>7),
    ]
    if r == 1:
        h = [h[1], h[0], h[2]]
    elif r == 2:
        h = [h[2], h[0], h[1]]
    return h


def _parse_koutsu(meld):
    # Adopted from http://tenhou.net/img/tehai.js
    unused = (meld &0x0060) >> 5
    t = (meld & 0xfe00) >> 9
    r = t % 3
    t = t // 3
    t *= 4
    h = [t, t, t]
    if unused == 0:
        h[0] += 1
        h[1] += 2
        h[2] += 3
    elif unused == 1:
        h[0] += 0
        h[1] += 2
        h[2] += 3
    elif unused == 2:
        h[0] += 0
        h[1] += 1
        h[2] += 3
    elif unused == 3:
        h[0] += 0
        h[1] += 1
        h[2] += 2
    if r == 1:
        h = [h[1], h[0], h[2]]
    elif r == 2:
        h = [h[2], h[0], h[1]]
    """
    kui = meld & 0x3
    if kui < 3:
        h = [h[2], h[0], h[1]]
    if kui < 2:
        h = [h[2], h[0], h[1]]
    """
    return h


def _parse_kakan(meld):
    # Adopted from http://tenhou.net/img/tehai.js
    added = (meld & 0x0060) >> 5
    t = (meld & 0xFE00) >> 9
    r = t % 3
    t = t // 3
    t *= 4
    h = [t, t, t]
    if added == 0:
        h[0] += 1
        h[1] += 2
        h[2] += 3
    elif added == 1:
        h[0] += 0
        h[1] += 2
        h[2] += 3
    elif added == 2:
        h[0] += 0
        h[1] += 1
        h[2] += 3
    elif added == 3:
        h[0] += 0
        h[1] += 1
        h[2] += 2
    if r == 1:
        h = [h[1], h[0], h[2]]
    elif r == 2:
        h = [h[2], h[0], h[1]]
    kui = meld & 0x3
    h = [t + added, h[0], h[1], h[2]]
    return h


def _parse_kan(meld):
    # Adopted from http://tenhou.net/img/tehai.js
    hai0 = (meld & 0xff00) >> 8
    kui = meld & 0x3
    if not kui:  # Ankan
        hai0 = (hai0 & ~3) +3
    t = (hai0 // 4) * 4
    h = [t, t, t]
    rem = hai0 % 4
    if rem == 0:
        h[0] += 1
        h[1] += 2
        h[2] += 3
    elif rem == 1:
        h[0] += 0
        h[1] += 2
        h[2] += 3
    elif rem == 2:
        h[0] += 0
        h[1] += 1
        h[2] += 3
    else:
        h[0] += 0
        h[1] += 1
        h[2] += 2
    """
    if kui == 1:
        hai0, h[2] = h[2], hai0
    if kui == 2:
        hai0, h[0] = h[0], hai0
    """
    return ([hai0] + h) if kui else h[:2]


def _parse_call(attrib):
    caller = int(attrib['who'])
    meld = int(attrib['m'])
    callee_rel = meld & 0x3
    if meld & (1 << 2):
        mentsu = _parse_shuntsu(meld)
        type_ = 'Chi'
    elif meld & (1 << 3):
        type_ = 'Pon'
        mentsu = _parse_koutsu(meld)
    elif meld & (1 << 4):
        type_ = 'KaKan'
        mentsu = _parse_kakan(meld)
    elif meld & (1 << 5):
        type_ = 'Nuki'
        mentsu = [meld >> 8]
    else:
        type_ = 'MinKan' if callee_rel else 'AnKan'
        mentsu = _parse_kan(meld)
    callee_abs = (caller + callee_rel) % 4
    return {
        'caller': caller, 'callee': callee_abs,
        'call_type': type_, 'mentsu': mentsu
    }


###############################################################################
def _parse_reach(attrib):
    who, step = int(attrib['who']), int(attrib['step'])
    if step > 2:
        raise NotImplementedError('Unexpected step value: {}'.format(attrib))

    result = {'player': who, 'step': step}
    # Old logs do not have ten values.
    if 'ten' in attrib:
        result['scores'] = _parse_score(attrib['ten'])
    return result


################################################################################
def _nest_list(vals):
    if len(vals) % 2:
        raise RuntimeError('List with odd number of value was given.')
    return list(zip(vals[::2], vals[1::2]))


def _parse_ba(val):
    vals = _parse_str_list(val, type_=int)
    return {'combo': vals[0], 'reach': vals[1]}


def _parse_owari(val):
    vals = _parse_str_list(val, type_=float)
    scores = [int(score * 100) for score in vals[::2]]
    return {'scores': scores, 'uma': vals[1::2]}


def _parse_ten(ten):
    vals = _parse_str_list(ten, type_=int)
    return {'fu': vals[0], 'point': vals[1], 'limit': vals[2]}


def _parse_sc(sc_val):
    vals = _parse_score(sc_val)
    return vals[::2], vals[1::2]


def _parse_agari(attrib):
    winner, from_who = int(attrib['who']), int(attrib['fromWho'])
    scores, gain = _parse_sc(attrib['sc'])
    result = {
        'winner': winner,
        'hand': _parse_str_list(attrib['hai'], type_=int),
        'machi': _parse_str_list(attrib['machi'], type_=int),
        'dora': _parse_str_list(attrib['doraHai'], type_=int),
        'ura_dora': _parse_str_list(
            attrib.get('doraHaiUra', ''), type_=int),
        'yaku': _nest_list(_parse_str_list(attrib.get('yaku'), type_=int)),
        'yakuman': _parse_str_list(attrib.get('yakuman', ''), type_=int),
        'ten': _parse_ten(attrib['ten']),
        'ba': _parse_ba(attrib['ba']),
        'scores': scores,
        'gains': gain,
    }
    if winner != from_who:
        result['loser'] = from_who
    if 'owari' in attrib:
        result['result'] = _parse_owari(attrib['owari'])
    return result


################################################################################
def _parse_dora(attrib):
    return {'hai': int(attrib['hai'])}


###############################################################################
def _parse_ryuukyoku(attrib):
    scores, gain = _parse_sc(attrib['sc'])
    result = {
        'hands': [
            _parse_str_list(attrib[key], type_=int) if key in attrib else None
            for key in ['hai0', 'hai1', 'hai2', 'hai3']
        ],
        'ba': _parse_ba(attrib['ba']),
        'scores': scores,
        'gains': gain,
    }
    if 'type' in attrib:
        result['reason'] = attrib['type']
    if 'owari' in attrib:
        result['result'] = _parse_owari(attrib['owari'])
    return result


###############################################################################
def _parse_bye(attrib):
    return {'index': int(attrib['who'])}


###############################################################################
def _ensure_unicode(data):
    return {
        ensure_unicode(key): ensure_unicode(value)
        for key, value in data.items()
    }


def parse_node(tag, attrib):
    """Parse individual XML node of tenhou mjlog.

    Parameters
    ----------
    tag : str
        Tags such as 'GO', 'DORA', 'AGARI' etc...

    attrib: dict or list
        Attribute of the node

    Returns
    -------
    dict
        JSON object
    """
    attrib = _ensure_unicode(attrib)
    if tag == 'GO':
        data = _parse_go(attrib)
    elif tag == 'UN':
        if len(attrib) == 1:  # Disconnected player has returned
            data = _parse_resume(attrib)
            tag = 'RESUME'
        else:
            data = _parse_un(attrib)
    elif tag == 'TAIKYOKU':
        data = _parse_taikyoku(attrib)
    elif tag == 'SHUFFLE':
        data = _parse_shuffle(attrib)
    elif tag == 'INIT':
        data = _parse_init(attrib)
    elif tag == 'DORA':
        data = _parse_dora(attrib)
    elif tag[0] in {'T', 'U', 'V', 'W'}:
        data = _parse_draw(tag)
        tag = 'DRAW'
    elif tag[0] in {'D', 'E', 'F', 'G'}:
        data = _parse_discard(tag)
        tag = 'DISCARD'
    elif tag == 'N':
        data = _parse_call(attrib)
        tag = 'CALL'
    elif tag == 'REACH':
        data = _parse_reach(attrib)
    elif tag == 'AGARI':
        data = _parse_agari(attrib)
    elif tag == 'RYUUKYOKU':
        data = _parse_ryuukyoku(attrib)
    elif tag == 'BYE':
        data = _parse_bye(attrib)
    else:
        raise NotImplementedError('{}: {}'.format(tag, attrib))
    return {'tag': tag, 'data': data}


###############################################################################
def _validate_structure(parsed, meta, rounds):
    # Verfiy all the items are passed
    if not len(parsed) == len(meta) + sum(len(r) for r in rounds):
        raise AssertionError('Not all the items are structured.')
    # Verfiy all the rounds start with INIT tag
    for round_ in rounds:
        tag = round_[0]['tag']
        if not tag == 'INIT':
            raise AssertionError('Round must start with INIT tag; %s' % tag)


def _structure_parsed_result(parsed):
    """Add structure to parsed log data

    Parameters
    ----------
    parsed : list of dict
        Each item in list corresponds to an XML node in original mjlog file.

    Returns
    -------
    dict
        On top level, 'meta' and 'rounds' key are defined. 'meta' contains
        'SHUFFLE', 'GO', 'UN' and 'TAIKYOKU' keys and its parsed results as
        values. 'rounds' is a list of which items correspond to one round of
        game play.
    """
    round_ = None
    game = {'meta': {}, 'rounds': []}
    for item in parsed:
        tag, data = item['tag'], item['data']
        if tag in ['SHUFFLE', 'GO', 'UN', 'TAIKYOKU']:
            game['meta'][tag] = data
        elif tag == 'INIT':
            if round_ is not None:
                game['rounds'].append(round_)
            round_ = [item]
        else:
            round_.append(item)
    game['rounds'].append(round_)

    _validate_structure(parsed, game['meta'], game['rounds'])
    return game


def parse_mjlog(root_node, tags=None):
    """Convert mjlog XML node into JSON

    Parameters
    ----------
    root_node (Element)
        Root node of mjlog XML data.

    tag : list of str
        When present, only the given tags are parsed and no post-processing
        is carried out.

    Returns
    -------
    dict
        Dictionary of of child nodes parsed.
    """
    parsed = []
    for node in root_node:
        if tags is None or node.tag in tags:
            parsed.append(parse_node(node.tag, node.attrib))
    if tags is None:
        return _structure_parsed_result(parsed)
    return parsed


translation = [
    "1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
    "1p", "2p", "3p", "4p", "5p", "6p", "7p", "8p", "9p",
    "1s", "2s", "3s", "4s", "5s", "6s", "7s", "8s", "9s",
    "E", "S", "W", "N", "P", "F", "C"
]

red = True

def translate(tile):
    ret = translation[tile >> 2] 
    if red and ret[0] == '5' and (tile & 3) == 0:
        return ret + 'r'
    else:
        return ret

import json

def parse_mjlog_to_mjai(root_node):
    parsed = parse_mjlog(root_node)
    game = parsed['meta']
    global red
    red = game['GO']['config']['red']
    if game['GO']['config']['sanma']:
        raise NotImplementedError("sanma")
    rounds = parsed['rounds']
    # {"type":"start_game","names":["UBS-AG","たがやす","そんし様","碧蓮"],
    # "kyoku_first":0,"aka_flag":true
    lines = [{"type": "start_game",
        "type": "start_game",
        "names": [i['name'] for i in game['UN']],
        "kyoku_first": 0 if game['GO']['config']['ton-nan'] else 4,
        "aka_flag": parsed['meta']['GO']['config']['red']
        }]
    for round_ in rounds:
        init = round_[0]['data']
        # from: {'tag': 'INIT', 
        # 'data': {'oya': '0', 'scores': [25000, 25000, 25000, 25000], 
        # 'hands': [[100, 57, 61, 98, 105, 106, 27, 30, 71, 99, 91, 24, 13], 
        # [40, 77, 0, 16, 3, 90, 47, 110, 120, 132, 14, 18, 119],
        #  [17, 6, 75, 28, 46, 127, 67, 121, 118, 83, 116, 34, 53], 
        # [33, 130, 101, 8, 85, 117, 9, 115, 25, 131, 103, 66, 12]],
        #  'round': 0, 'combo': 0, 'reach': 0, 'dices': [0, 4], 'dora': 81}}
        
        # to: {"type":"start_kyoku","bakaze":"E","dora_marker":"3s",
        # "kyoku":1,"honba":0,"kyotaku":0,
        # "oya":0,"scores":[25000,25000,25000,25000],
        # "tehais":[["4m","7m","7m","8m","6p","7p","9p","5s","7s","7s","8s","9s","9s"],
        # ["1m","1m","4m","5m","5mr","2p","3p","2s","5s","E","W","N","C"],
        # ["2m","5m","8m","9m","3p","5p","8p","1s","3s","W","W","N","P"],
        # ["3m","3m","4m","7m","9m","8p","4s","8s","8s","S","W","F","F"]]}
        lines.append({"type": "start_kyoku",
            "bakaze": "ESWN"[int(init['round'] // 4)  % 4],
            "dora_marker": translate(int(init['dora'])),
            "kyoku": int(init['round']) % 4 + 1,
            "honba": int(init['combo']),
            "kyotaku": int(init['reach']),
            "oya": int(init['oya']),
            "scores": init['scores'],
            "tehais": [[translate(i) for i in sorted(j, key=lambda x:x^3)] for j in init['hands']] # xor 3 to make 5m 5mr correct
        })
        lastdraw = -1
        ura_marker = []
        pon = {}
        need_dora = []
        reach_accepted = 0
        for value in round_[1:]:
            tag = value['tag']
            data = value['data']
            if tag == 'BYE':
                continue
            elif tag == 'RESUME':
                continue
            elif tag == 'DRAW' :
                # from: {'tag': 'DRAW', 'data': {'player': 0, 'tile': 106}}
                # to: {"type":"tsumo","actor":0,"pai":"9s"}
                lines.append({"type": "tsumo",
                    "actor": int(data['player']),
                    "pai": translate(int(data['tile']))
                })
                lastdraw = int(data['tile'])
            elif tag == 'DISCARD':
                lines.append({"type": "dahai",
                    "actor": int(data['player']),
                    "pai": translate(int(data['tile'])),
                    "tsumogiri": int(data['tile']) == lastdraw
                })
            elif tag == 'CALL':
                lastdraw = -1
                # from: {'tag': 'CALL', 'data': {'caller': 1, 'callee': 1, 'call_type': 'AnKan', 'mentsu': [124, 125]}}
                # to: {"type":"ankan","actor":1,"consumed":["P","P","P","P"]}
                if data['call_type'] == 'Pon':
                    # {'tag': 'CALL', 'data': {'caller': 3, 'callee': 1, 'call_type': 'Pon', 'mentsu': [111, 108, 109]}}
                    # {"type":"pon","actor":3,"target":1,"pai":"E","consumed":["E","E"]}
                    lines.append({"type": "pon",
                        "actor": int(data['caller']),
                        "target": int(data['callee']),
                        "pai": translate(data['mentsu'][0]),
                        "consumed": [translate(i) for i in sorted([data['mentsu'][i] for i in range(1, 3)], key=lambda x:x^3)]
                    })
                    pon[data['mentsu'][0] // 4] = [lines[-1]["pai"]]
                    pon[data['mentsu'][0] // 4].extend(lines[-1]["consumed"])
                elif data['call_type'] == 'Chi':
                    lines.append({"type": "chi",
                        "actor": int(data['caller']),
                        "target": int(data['callee']),
                        "pai": translate(data['mentsu'][0]),
                        "consumed": [translate(i) for i in sorted([data['mentsu'][i] for i in range(1, 3)], key=lambda x:x^3)]
                    })
                elif data['call_type'] == 'AnKan':
                    lines.append({"type": "ankan",
                        "actor": int(data['caller']),
                        "consumed": [translate(data['mentsu'][0] // 4 * 4 + 3 - i) for i in range(4)]
                    })
                    need_dora.append(len(lines) - 1)
                elif data['call_type'] == 'MinKan':
                    lines.append({"type": "daiminkan",
                        "actor": int(data['caller']),
                        "target": int(data['callee']),
                        "pai": translate(data['mentsu'][0]),
                        "consumed": [translate(i) for i in sorted([data['mentsu'][i] for i in range(1, 4)], key=lambda x:x^3)]
                    })
                    need_dora.append(len(lines) - 1)
                elif data['call_type'] == 'KaKan':
                    lines.append({"type": "kakan",
                        "actor": int(data['caller']),
                        "pai": translate(data['mentsu'][0]),
                        "consumed": pon[data['mentsu'][0] // 4].copy()
                    })
                    pon[data['mentsu'][0] // 4].clear()
                    need_dora.append(len(lines) - 1)
            elif tag == 'REACH':
                if data['step'] == 1:
                    lines.append({"type": "reach",
                        "actor": int(data['player'])
                    })
                else:
                    reach_accepted += 1
                    if reach_accepted < 4:
                        lines.append({"type": "reach_accepted",
                            "actor": int(data['player'])
                        })
            elif tag == 'AGARI':
                # {'tag': 'AGARI', 'data': 
                # {'winner': 0, 'hand': [22, 24, 30, 55, 57, 61, 88, 94, 98, 99, 100, 105, 106, 107], 'machi': [88], 'dora': [81], 'ura_dora': [89], 'yaku': [(1, 1), (0, 1), (7, 1), (54, 1), (53, 1)],
                # 'yakuman': [], 'ten': {'fu': 20, 'point': 12000, 'limit': 1}, 'ba': 
                # {'combo': 0, 'reach': 2}, 'scores': [24000, 24000, 25000, 25000], 'gains': [14000, -4000, -4000, -4000]}}]

                # {"type":"hora","actor":0,"target":0,"deltas":[14000,-4000,-4000,-4000],"ura_markers":["5s"]}
                line = {"type": "hora",
                    "actor" : int(data['winner']),
                    "target": int(data['loser']) if 'loser' in data else int(data['winner']),
                    "deltas": data['gains'],
                    "ura_markers" : ura_marker # double hora, one is reach, the other could use the ura dora
                }
                if "ura_dora" in data and len(data['ura_dora']) > 0 and len(ura_marker) == 0:
                    ura_marker.extend([translate(i) for i in data['ura_dora']])
                if len(line['ura_markers']) > 0:
                    i = len(lines) - 1
                    while i >= 0 and lines[i]['type'] == 'hora':
                        lines[i]['ura_markers'] = line['ura_markers']
                        i -= 1
                lines.append(line)
            elif tag == 'DORA':
                assert (len(need_dora) > 0)
                w = 3 if len(need_dora) > 1 and lines[need_dora[0] + 2]['type'] == 'kakan' else 2
                lines.insert(need_dora.pop(0) + w, {"type": "dora",
                    "dora_marker": translate(int(data['hai']))
                })
                need_dora = [i + 1 for i in need_dora]
            else:
                assert (tag == 'RYUUKYOKU')
                lines.append({"type": "ryukyoku",
                        "deltas": data['gains']})
        
        lines.append({"type": "end_kyoku"})
    lines.append({"type": "end_game"})
    return '\n'.join(json.dumps(line, separators=(',', ':'), ensure_ascii=False) for line in lines)